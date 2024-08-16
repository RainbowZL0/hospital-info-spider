import time
from colorama import Fore, init
import joblib
import numpy
import pandas as pd
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

EXCEL_PATH = './县级.xlsx'
OUTPUT_PATH = './hospital_县级.xlsx'
init(autoreset=True)

class HospitalBuiltTime:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.action = ActionChains(self.driver)
        self.wait = WebDriverWait(self.driver, 3)  # 创建一个wait对象

        self.df = pd.read_excel(EXCEL_PATH)
        self.hospital_name_list = None

        self.built_time_list = list()

    def save_cookies(self):
        self.driver.get("https://baike.baidu.com/")

        time.sleep(10)

        cookies = self.driver.get_cookies()
        joblib.dump(cookies, 'cookies.jbl')

    def load_cookies(self):
        self.driver.get("https://baike.baidu.com/")
        cookies = joblib.load('cookies.jbl')

        self.driver.delete_all_cookies()
        for cookie in cookies:
            self.driver.add_cookie(cookie)

        self.driver.refresh()
        self.driver.get("https://baike.baidu.com/item/%E5%86%85%E6%B1%9F%E5%B8%82%E7%AC%AC%E4%B8%80%E4%BA%BA%E6%B0%91"
                        "%E5%8C%BB%E9%99%A2?fromModule=lemma_search-box")

    def get_hospital_name_list(self):
        # column_name = self.df.columns[3]
        # self.hospital_name_list = self.df[column_name]
        self.hospital_name_list = self.df['医院名称']

    def input_hospital_and_jump(self, hospital_name):
        """

        :param hospital_name:
        :type hospital_name:
        :return:
        :rtype:
        """
        # 等待搜索框出现
        search_class_finder = (By.CLASS_NAME, 'form')
        # try:
        #     search_class = self.wait.until(ec.visibility_of_element_located(search_class_finder))
        # except AssertionError as e:
        #     print(e)

        time.sleep(0.5)

        while not self.has_element(search_class_finder):
            self.driver.refresh()
        search_class = self.driver.find_element(By.CLASS_NAME, 'form')

        # 找到输入框，并输入查询的医院
        input_frame_inner = search_class.find_element(
            By.CLASS_NAME,
            'input-wrap.J-input-wrap'
        ).find_element(
            By.TAG_NAME,
            'input'
        )
        input_frame_inner.clear()
        input_frame_inner.send_keys(hospital_name)

        # 点击搜索跳转
        possible_enter_buttons_list = search_class.find_elements(
            By.TAG_NAME,
            'button'
        )
        enter_button = None
        for button in possible_enter_buttons_list:
            if button.text == "进入词条":
                enter_button = button
                break
        assert enter_button is not None  # 确保找到了按钮
        enter_button.click()  # 点击

    def input_hospital_and_jump_v2(self, hospital_name):
        pass

    def get_built_time(self):
        """
        已经跳转到搜索结果页面后，获取当前医院的建院时间信息
        :return: 建院时间
        :rtype:
        """
        if self.has_page():
            possible_built_time_list = self.driver.find_elements(
                By.CLASS_NAME,
                'basicInfo-item.name'
            )
            # 找到建立时间相关的那一项
            built_time_item = None
            for item in possible_built_time_list:
                if item.text in ["成立时间",
                                 "建立时间",
                                 "建院时间", 
                                 "创建日期",
                                 "始建于",
                                 "创建时间",
                                 "创建于"]:
                    built_time_item = item
                    break

            if built_time_item is not None:  # 如果条目上有时间信息项
                # 定位到时间内容本身
                built_time = built_time_item.find_element(
                    By.XPATH,
                    'following-sibling::dd'
                ).text
                built_time = clean_years_format(built_time)  # 格式转换
            else:  # 若没有时间信息，设为空串
                built_time = "no item"
        else:
            built_time = "no page"

        print(f"{Fore.GREEN}{built_time}")
        self.built_time_list.append(built_time)

    def has_page(self):
        """
        已经跳转到搜索结果页面后，判断百度百科词条是否有该条目。
        :return: 是或否
        :rtype: bool
        """
        # 等待元素出现
        body_elem_finder = (By.TAG_NAME, 'body')
        body_elem = self.wait.until(ec.presence_of_element_located(body_elem_finder))
        # 获取class属性的内容，判断是不是有效的条目页面
        body_elem_class = body_elem.get_attribute('class')

        while body_elem_class == "":
            self.driver.refresh()
            body_elem_class = self.driver.find_element(
                By.TAG_NAME,
                'body'
            ).get_attribute('class')

        valid_class = ["wiki-lemma neweditor normal",
                       "wiki-lemma neweditor feature small-feature hospital",
                       "wiki-lemma  normal"]
        if body_elem_class in valid_class:
            bool_has_page = True
        else:
            bool_has_page = False
        return bool_has_page

    def update_built_time_column_and_output(self):
        array = numpy.array(self.built_time_list)
        self.df["建院时间"] = array

        self.df.to_excel(OUTPUT_PATH)

    def has_element(self, elem_finder: tuple):
        by, name = elem_finder
        elems = self.driver.find_elements(by, name)
        if len(elems) == 0:
            return False
        else:
            return True


def clean_years_format(string: str):
    # return re.sub('年',  # 被替换的内容
    #               '',  # 替换成？
    #               string)  # 应用处理的字符串
    return string[:4]


def start():
    hospital = HospitalBuiltTime()
    hospital.load_cookies()
    hospital.get_hospital_name_list()

    sum = 0
    for hospital_name in hospital.hospital_name_list:
        hospital.input_hospital_and_jump(hospital_name)
        hospital.get_built_time()
        
        if sum % 100 == 0:
            file_name = f'{sum}_built_time_list.jbl'
            joblib.dump(hospital.built_time_list, file_name)
        sum += 1

    hospital.update_built_time_column_and_output()

    hospital.driver.close()


def df_test():
    df = pd.read_excel(EXCEL_PATH)
    print(df.columns)
    # column_name = df.columns[3]
    # column = df[column_name]
    # print(column)


if __name__ == '__main__':
    start()
