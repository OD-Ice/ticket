import asyncio
from headers_pool import User_Agent
import random
import aiohttp
import requests
import datetime
from citycode import City
# from pprint import pprint
import time
import pandas as pd
import prettytable as pt


class Ticket:
    def __init__(self):
        self.start_url = 'https://kyfw.12306.cn/otn/leftTicket/query'
        self.user_agents = User_Agent()
        self.writer = pd.ExcelWriter('车次信息.xlsx')

    async def get_page(self, date, from_city, to_city, is_adult, cookies):
        time.sleep(1)
        user_agent = random.choice(self.user_agents.user_agents)
        headers = {'User-Agent': user_agent}

        params = {
            'leftTicketDTO.train_date': date,
            'leftTicketDTO.from_station': from_city,
            'leftTicketDTO.to_station': to_city,
            'purpose_codes': is_adult  # ADULT/0X00
        }
        async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
            async with await session.get(self.start_url, params=params) as res:
                result = await res.json()
                return [result, date]

    def get_cookies(self):
        user_agent = random.choice(self.user_agents.user_agents)
        headers = {'User-Agent': user_agent}
        url = f'https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc&fs=%E9%83%91%E5%B7%9E,ZZF&ts=%E5%8C%97%E4%BA%' \
              f'AC,BJP&date={datetime.datetime.now().strftime("%Y-%m-%d")}&flag=N,N,Y'
        res = requests.get(url, headers=headers)
        print('获取cookies...')
        return res.cookies

    @staticmethod
    def get_keys(value):
        city = City()
        return str([k for k, v in city.city.items() if v == value]).strip("['").strip("']")

    def parse(self, t):
        tb = pt.PrettyTable()
        tb.field_names = [
            '车次',
            '始发站',
            '终点站',
            '出发地',
            '目的地',
            '出发时间',
            '到达时间',
            '历时',
            '特等座 商务座',
            '一等座',
            '二等座 二等包座',
            '高级软卧',
            '软卧 一等卧',
            '动卧',
            '硬卧 二等卧',
            '硬座',
            '无座'
        ]
        data = t.result()[0]['data']['result']
        data_dict = {
            '车次': [],
            '始发站': [],
            '终点站': [],
            '出发地': [],
            '目的地': [],
            '出发时间': [],
            '到达时间': [],
            '历时': [],
            '特等座 商务座': [],
            '一等座': [],
            '二等座 二等包座': [],
            '高级软卧': [],
            '软卧 一等卧': [],
            '动卧': [],
            '硬卧 二等卧': [],
            '硬座': [],
            '无座': []
        }
        for each in data:
            data_list = each.split('|')
            # 车次
            train_number = data_list[3]
            # 始发站
            departure_station = self.get_keys(data_list[4])
            # 终点站
            terminus = self.get_keys(data_list[5])
            # 出发地
            from_city = self.get_keys(data_list[6])
            # 目的地
            to_city = self.get_keys(data_list[7])
            # 出发时间
            starting_time = data_list[8] if data_list[1] == '预订' else '列车停运'
            # 到达时间
            ending_time = data_list[9] if data_list[1] == '预订' else '-'
            # 历时
            duration = data_list[10] if data_list[1] == '预订' else '-'
            if duration != '-':
                duration_time = datetime.timedelta(hours=int(duration.split(':')[0]),
                                                   minutes=int(duration.split(':')[1]))
                total_time = datetime.timedelta(days=1)
                start_time = datetime.datetime.strptime(starting_time, '%H:%M')
                zero_time = datetime.datetime.strptime('00:00', '%H:%M')
                dif_time = total_time - (start_time - zero_time)
                if duration_time < dif_time:
                    ending_time = f'当日到达 {ending_time}'
                elif duration_time < dif_time + total_time:
                    ending_time = f'次日到达 {ending_time}'
                elif duration_time < dif_time + 2 * total_time:
                    ending_time = f'两日到达 {ending_time}'
                else:
                    ending_time = f'三日到达 {ending_time}'
            # 特等座 商务座
            business_class = data_list[32] if data_list[32] != '' else '-'
            # 一等座
            first_class = data_list[31] if data_list[31] != '' else '-'
            # 二等座 二等包座
            second_class = data_list[30] if data_list[30] != '' else '-'
            # 高级软卧
            soft_beds = data_list[21] if data_list[21] != '' else '-'
            # 软卧 一等卧
            first_beds = data_list[23] if data_list[23] != '' else '-'
            # 动卧
            move_beds = data_list[33] if data_list[33] != '' else '-'
            # 硬卧 二等卧
            hard_beds = data_list[28] if data_list[28] != '' else '-'
            # 硬座
            hard_seats = data_list[29] if data_list[29] != '' else '-'
            # 无座
            no_seats = data_list[26] if data_list[26] != '' else '-'

            # prettytable
            tb.add_row([train_number, departure_station, terminus, from_city, to_city, starting_time,
                        ending_time, duration, business_class, first_class, second_class,
                        soft_beds, first_beds, move_beds, hard_beds, hard_seats, no_seats])

            data_dict['车次'].append(train_number)
            data_dict['始发站'].append(departure_station)
            data_dict['终点站'].append(terminus)
            data_dict['出发地'].append(from_city)
            data_dict['目的地'].append(to_city)
            data_dict['出发时间'].append(starting_time)
            data_dict['到达时间'].append(ending_time)
            data_dict['历时'].append(duration)
            data_dict['特等座 商务座'].append(business_class)
            data_dict['一等座'].append(first_class)
            data_dict['二等座 二等包座'].append(second_class)
            data_dict['高级软卧'].append(soft_beds)
            data_dict['软卧 一等卧'].append(first_beds)
            data_dict['动卧'].append(move_beds)
            data_dict['硬卧 二等卧'].append(hard_beds)
            data_dict['硬座'].append(hard_seats)
            data_dict['无座'].append(no_seats)

        data_pd = pd.DataFrame(data_dict)
        sheet_name = t.result()[1]
        print(sheet_name)
        print(tb)
        print('=' * 100)
        data_pd.to_excel(self.writer, sheet_name=sheet_name, index=False)

    async def run(self):
        tasks = []
        city = City()
        from_city = city.city[input('出发地：')]
        to_city = city.city[input('目的地：')]
        des = input('成人票/学生票（A/S）：')
        is_adult = 'ADULT' if des == 'A' or des == 'a' else '0X00' if des == 'S' or des == 's' else None
        cookies = self.get_cookies()

        start_date = input('请输入出发日期(xxxx-xx-xx)：')
        start_date = time.strftime('%Y-%m-%d', time.strptime(start_date, '%Y-%m-%d'))
        end_date = input('请输入返程日期(xxxx-xx-xx)\n没有请输入"N"：')
        if end_date in ['n', 'N']:
            dates = [start_date]
        else:
            end_date = time.strftime('%Y-%m-%d', time.strptime(end_date, '%Y-%m-%d'))
            dates = [start_date, end_date]
        for date in dates:
            c = self.get_page(date=date, from_city=from_city, to_city=to_city, is_adult=is_adult, cookies=cookies)
            from_city, to_city = to_city, from_city
            task = asyncio.create_task(c)
            task.add_done_callback(self.parse)
            tasks.append(task)
        await asyncio.wait(tasks)

    def save(self):
        self.writer.save()


if __name__ == '__main__':
    start = time.time()
    ticket = Ticket()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ticket.run())
    ticket.save()
    print('总耗时：', time.time() - start)
