from time import sleep
import pychrome


browser = pychrome.PyChrome()
browser.open("http://https://chatgpt.com")

# # create a browser instance
# browser = pychrome.Browser(url="http://127.0.0.1:9222")

# # create a tab
# tab = browser.new_tab()


# # register callback if you want
# def request_will_be_sent(**kwargs):
#     print("loading: %s" % kwargs.get("request").get("url"))


# tab.Network.requestWillBeSent = request_will_be_sent

# # start the tab
# tab.start()
# print(1)
# # call method
# tab.Network.enable()
# # call method with timeout
# tab.Page.navigate(url="https://chatgpt.com", _timeout=5)
# print(2)
# # wait for loading
# tab.wait(10)
# print(3)
# # stop the tab (stop handle events and stop recv message from chrome)
# # tab.stop()
# print(4)
# # close tab
# # browser.close_tab(tab)
# print(5)
# # sleep(10)
