import requests, re, random
from lxml import etree


class Customer:
    def __init__(self):
        self.__domain = 'https://www.qcc.com'
        self.__user_agent = [
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)'
        ]
        self.__headers = self.__get_headers()

    def __get_headers(self):
        user_agent = random.choice(self.__user_agent)
        url = '%s/?utm_source=baidu1&utm_medium=cpc&utm_term=cqy' % self.__domain
        headers = {'user-agent': user_agent}
        resp_cookie = requests.get(url=url, headers=headers)
        cookie = resp_cookie.headers['Set-Cookie']
        acw_tc = re.findall('acw_tc=(.*?);', cookie)[0]
        QCCSESSID = re.findall('QCCSESSID=(.*?);', cookie)[0]
        cookie = 'acw_tc=%s;QCCSESSID=%s' % (acw_tc, QCCSESSID)
        return {
            'user-agent': user_agent,
            'cookie': cookie
        }

    def __send_requests(self, urls):
        response = requests.get(url=urls, headers=self.__headers)
        xph = etree.HTML(response.text)
        return xph

    def __get_cusurl(self, cusname):
        url = '%s/web/search?key=%s' % (self.__domain, cusname)
        cus_html = self.__send_requests(url)
        cus_url = cus_html.xpath("//div[@class='maininfo']/a[1]/@href")
        cus_url = '%s/cbase/%s' % (self.__domain, cus_url[0].split('/')[-1]) if cus_url else ''
        return cus_url

    def get_infomation(self, cusname):
        url = self.__get_cusurl(cusname)
        info_html = self.__send_requests(url)
        table = info_html.xpath("//section[@id='cominfo']//table[@class='ntable']//td")
        table = table if len(table) // 2 else table.append('')
        key = table[::2]
        value = table[1::2]
        key = [td.text.strip().replace('：', '') if td.text else '' for td in key]
        value = [td.text.strip() if td.text else '' for td in value]
        return dict(zip(key, value))

    @staticmethod
    def chg(currency):
        unit = ''
        num = ''
        if 'CNY' in currency:
            unit = '万人民币'
            num = float(currency.split('CNY')[0].replace(',', '')) / 10000 if currency.split('CNY') else ''
            return num, unit
        if '万元人民币' in currency:
            unit = '万人民币'
            num = float(currency.split('万')[0].replace(',', '')) if currency.split('万') else ''
        return num, unit


if __name__ == '__main__':
    req = Customer()
    info = req.get_infomation('深圳市元征科技股份有限公司')
    print(req.chg(info.get('注册资本', '')), req.chg(info.get('实缴资本', '')))

