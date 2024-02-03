from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CardListing:
    def __init__(self, card_name, base_price, shipping_price, condition, seller_name, is_cert_shop, is_gold_star, is_direct, seller_rating, seller_sales, page):
        self.card_name = card_name
        self.base_price = base_price
        self.condition = condition
        self.shipping_price = shipping_price
        self.seller_name = seller_name
        self.is_cert_shop = is_cert_shop
        self.is_gold_star = is_gold_star
        self.is_direct = is_direct
        self.seller_rating = seller_rating
        self.seller_sales = seller_sales
        self.page = page
    
    def __repr__(self):
        return f"""------------------
        {self.card_name}
        ${self.base_price}
        {self.condition}
        ${self.shipping_price}
        {self.seller_name}
        {self.seller_rating}%
        "{self.seller_sales} sales
        IsCert: {self.is_cert_shop}
        IsGold: {self.is_gold_star}
        Page: {self.page}"""

    def __eq__(self, other):
        return self.card_name == other.card_name and \
        self.base_price == other.base_price and \
        self.condition == other.condition and \
        self.shipping_price == other.shipping_price and \
        self.seller_name == other.seller_name and \
        self.seller_rating == other.seller_rating and \
        self.seller_sales == other.seller_rating and \
        self.is_cert_shop == other.is_cert_shop and \
        self.is_gold_star == other.is_gold_star and \
        self.is_direct == other.is_direct and \
        self.page == other.page
    
    def __str__(self):
        return self.__repr__()

    def price(self):
        return self.base_price + self.shipping_price

    
def normalize_price(price_str):
    price_split = price_str.split(",")
    price_no_comma = "".join(price_split)
    return float (price_no_comma)


def get_shipping_price(item_info_elem):
    price_info = item_info_elem.text.split('\n')
    shipping_str = price_info[1]
    if(shipping_str == "Shipping: Included"):
        return 0
    
    #Calculate based on TCG Direct Estimates
    if(shipping_str == "Free Shipping on Orders Over $50"):
        return 5
    
    shipping_price_str = shipping_str.split(" ")[1]
    shipping_price = shipping_price_str[1:]
    return normalize_price(shipping_price)

#This function either mines all of the prices for a given card 
# or it navigates to the page a target CardListing object is located on
# If no target card is passed in, this function returns list of CardListing objects
# If target card is passed, it returns the CardListing of the target, meaning the browser is on its page
# If the target card can't be found, it returns None
def mine_prices(driver, card_url, page_scrape_limit=3, target_card=None):
    driver.get(card_url)

    try:

        try:
            survey_box_elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".QSIWebResponsive"))
            )

            if(survey_box_elem):
                buttons = survey_box_elem.find_elements(By.CSS_SELECTOR, ".QSIWebResponsiveDialog-Layout1-SI_9sGiASCdwhTfH1k_button-border-radius-slightly-rounded")
                no_thanks_button = buttons[1]
                no_thanks_button.click()

        finally:
            listing_objs = []

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".listing-item"))
            )

            pagination_buttons = driver.find_element(By.CSS_SELECTOR, ".search-pagination")
            page_buttons = pagination_buttons.find_elements(By.CSS_SELECTOR, ".tcg-button")
            
            max_page = int ((page_buttons[len(page_buttons)-2]).text)

            card_name = driver.find_element(By.CSS_SELECTOR, ".product-details__name").text
            print(card_name)

            if(max_page > page_scrape_limit):
                max_page = page_scrape_limit

            i=0
            while i < max_page:
                pagination_buttons = driver.find_element(By.CSS_SELECTOR, ".search-pagination")
                page_buttons = pagination_buttons.find_elements(By.CSS_SELECTOR, ".tcg-button")
                next_button = page_buttons[len(page_buttons)-1]
            
                listings = driver.find_elements(By.CSS_SELECTOR, ".listing-item")
                for listing in listings:
                    item_info_elem = listing.find_element(By.CSS_SELECTOR, ".listing-item__info")
                    base_price_str = item_info_elem.find_element(By.CSS_SELECTOR, ".listing-item__price").text
                    base_price = normalize_price(base_price_str[1:])
                    shipping_price = get_shipping_price(item_info_elem)
                    condition = listing.find_element(By.CSS_SELECTOR, ".listing-item__condition").text
                    seller_name = listing.find_element(By.CSS_SELECTOR, ".seller-info__name").text
                    seller_info = listing.find_element(By.CSS_SELECTOR, ".seller-info__content")
                    seller_info_a_tags = seller_info.find_elements(By.TAG_NAME, "a")

                    is_cert_shop = False
                    is_gold_star = False
                    is_direct = True
                    for tag in seller_info_a_tags:
                        title = tag.get_attribute("title")
                        if(title == "Certified Hobby Shop"):
                            is_cert_shop = True
                        if(title == "Gold Star Seller"):
                            is_gold_star = True
                        if(title == "Direct Seller"):
                            is_direct = True
                                
                    seller_rating_str = listing.find_element(By.CSS_SELECTOR, ".seller-info__rating").text
                    seller_rating = seller_rating_str[:-1]
                    seller_sales_str = listing.find_element(By.CSS_SELECTOR, ".seller-info__sales").text
                    seller_sales = seller_sales_str.split(" ")[0][1:]
                    page = i+1
                    card_listing = CardListing(card_name, base_price, shipping_price, condition, seller_name, is_cert_shop, is_gold_star, is_direct, seller_rating, seller_sales, page)
                    
                    if(target_card and card_listing == target_card):
                        return card_listing
                    
                    listing_objs.append(card_listing)

                i+=1
                if(i < max_page): # Don't reload on the last page
                    next_button.click()
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".listing-item"))
                    )
            
    finally:
        print("finished.")
        
    if(target_card):
        return None
    return listing_objs


def get_lowest_price_p_shipping(card_listing_list, gold_star_filter=False):
    if(gold_star_filter):
        i=0
        while(i<len(card_listing_list)-1):
            if(card_listing_list[i].is_gold_star):
                lowest_card = card_listing_list[i]
                break
        if(i==len(card_listing_list)-1):
            return None
    else:
        lowest_card = card_listing_list[0]

    for listing in card_listing_list:

        #If gold star filter is enabled and not gold star, skip it
        if(gold_star_filter and not listing.is_gold_star):
            continue
        
        if(listing.price() < lowest_card.price()):
            lowest_card = listing
    return lowest_card



def buy_card(CardListing):
    print("Buying...")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".listing-item"))
    )




def main():
    card_url = "https://www.tcgplayer.com/product/215686/magic-core-set-2021-colossal-dreadmaw?xid=pi34ba7d05-ec0f-4edc-b14e-82c4a99448c7&page=1&Language=English"
    page_scrape_limit = 1

    driver = webdriver.Firefox()
    listings = mine_prices(driver, card_url, page_scrape_limit)

    lowest_listing = get_lowest_price_p_shipping(listings)
    print(lowest_listing)
    # for listing in listings:
    #         print(listing)

    
    #driver.close()

# assert "Python" in driver.title
# elem = driver.find_element(By.NAME, "q")
# elem.clear()
# elem.send_keys("pycon")
# elem.send_keys(Keys.RETURN)
# assert "No results found." not in driver.page_source
# driver.close()

if __name__ == '__main__':
    main()