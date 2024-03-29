# -*- coding: utf-8 -*-
"""
update.py

Create and update stock database

"""
import datetime
import requests
import sys
from collections import defaultdict
from os.path import isfile
from os import remove
from bs4 import BeautifulSoup
from tqdm import tqdm
from multiprocessing import Process, Lock, Queue
import pickle
import time

from kostock.stockdb import StockDB
from kostock import qutils
from kostock import kiwoom
from kostock import logs
from kostock import data
from kostock.configurer import Configurer


class Update:
    def run(self):
        # freeze_support()
        log = logs.Log()
        logger = log.config_log(Configurer.UPDATE_LOG_PATH, name='file')
        db = StockDB()
        with db:
        # Init Update
            is_init = self.check_init(db=db)
            if is_init:
                logger.info('Init update start...')
                self.update_init(db=db)
            else:
                logger.info("Init update already done...")

            # Stock Info table Update
            sinfo_date, chart_date = self.get_update_date()
            if self.check_sinfo_update(db=db, update_date=sinfo_date):
                logger.info('Stock info update start...')
                self.update_sinfo_and_schema(db=db, update_date=sinfo_date)
                if self.check_manual_transfer():
                    logger.info('To transfer chart data manually, update end...')
                    return
            else:
                logger.info('Stock info update is not necessary > skipped')

            # Chart table Update
            update_dict = self.get_chart_update_dict(db=db, update_date=chart_date)

        if update_dict:
            logger.info('Chart update start...')
            self.update_chart_tables(db=db, update_dict=update_dict, update_date=chart_date)
        else:
            logger.info('Chart table update is not necessary > skipped')
        logger.info('All update is done...')

    def check_init(self, db):
        sql = 'show tables;'
        db.cur.execute(sql)
        tables = db.cur.fetchall()
        if not tables:
            is_init = True
        else:
            is_init = False
        return is_init

    def update_init(self, db):
        db.create_meta_schema()
        db.create_sinfo_schema()

    def get_update_date(self):
        update_date = Configurer.UPDATE_END_DATE
        if update_date is None:
            update_date = datetime.date.today()
        else:
            update_date = datetime.datetime.strptime(update_date, '%Y-%m-%d').date()

        chart_update_date = qutils.get_latest_trading_date(update_date,
                                                           data.HOLIDAY_URL,
                                                           Configurer.UPDATE_HOLIDAY_KEY)
        sinfo_update_date = chart_update_date - datetime.timedelta(days=1)
        sinfo_update_date = qutils.get_latest_trading_date(sinfo_update_date,
                                                           data.HOLIDAY_URL,
                                                           Configurer.UPDATE_HOLIDAY_KEY)
        # sinfo update date is based on WICS index and its website process update at almost 3AM.
        # So previous day will be chosen to be sinfo update date.
        return [sinfo_update_date, chart_update_date]

    def check_sinfo_update(self, db, update_date):
        latest_sinfo = db.get_sinfo_from_meta()
        whether_update = False
        if latest_sinfo is None:
            whether_update = True
        elif update_date - latest_sinfo[1] >= datetime.timedelta(days=30):
            whether_update = True
        return whether_update

    def update_sinfo_and_schema(self, db, update_date):
        # there is no data in the stock market closed day and before market open.
        # weekends, Jan 1, Dec 31 etc

        logger = logs.Log().get_logger('file')
        old_code_list = tuple(i[0] for i in db.get_code_list_from_sinfo())
        new_code_list = []
        only_new_list = []
        with tqdm(total=100, ascii=True, desc='Sinfo Table UPDATE') as pbar:
            # [pbar 80%] update stock info table
            one_wics = 80 / len(data.WICS_MC.keys()) # 80%
            for wics_code in data.WICS_MC.keys():
                response = requests.get(qutils.get_url(data.WICS_URL, update_date, wics_code))
                if response.status_code == 200:  #
                    json_list = response.json()  # dictionary
                    # response.text -> return str type
                    for json in json_list['list']:
                        ls = json['SEC_NM_KOR']  # Large sector
                        ms = json['IDX_NM_KOR'][5:]  # Medium sector
                        code = json['CMP_CD']  # Company code
                        name = json['CMP_KOR']  # Company korean name
                        market, num_stocks = self.crowling_market_and_numstocks(code)
                        #market = kiwoom.get_master_stock_info(code,)[0][0]
                        #num_stocks = kiwoom.get_master_listed_stock_cnt(code)
                        db.add_row_into_sinfo(code=code, name=name, wics_ls=ls,
                                              wics_ms=ms, market=market, num_stocks=num_stocks)
                        new_code_list.append(code)
                        if code not in old_code_list:
                            only_new_list.append(code)
                        pbar.update(one_wics / len(json_list['list']))
                else:
                    logger.error('request fail status={0}, WICS_code={1}'.format(response.status_code, wics_code))
                    pbar.update(one_wics)
                db.commit()

            # [pbar 10%] create chart schema
            for code in only_new_list:
                db.create_chart_schema(code=code)
                listing_date = self.crowling_listing_date(code=code)
                db.insert_listing_date_into_meta(code=code, listing_date=listing_date)
                pbar.update(10 / len(only_new_list)) # 10%

            # [pbar 9%] remove old data (sinfo row, chart table, meta row)
            for old_code in old_code_list:
                if old_code not in new_code_list:
                    db.delete_row_from_sinfo(code=old_code)
                    db.delete_chart_table_from_meta(code=old_code)
                    db.drop_chart_schema(code=old_code)
                pbar.update(9 / len(old_code_list)) # 9%

            # [pbar 1%] commit
            db.update_sinfo_date_in_meta(update_date=update_date)
            db.commit()
            pbar.update(1)

    def crowling_market_and_numstocks(self, code):
        logger = logs.Log().get_logger('file')
        html = requests.get(qutils.get_url(data.COMPANY_MAIN_URL, code))
        if html.status_code == 200:
            bs = BeautifulSoup(html.text, 'html.parser')
            market = bs.select_one('.stxt1').text
            num_stocks = bs.select_one('.us_table_ty1.table-hb.thbg_g.h_fix.zigbg_no ' + \
                                       'tr:nth-last-of-type(1) > td:nth-of-type(1)').text
            if 'KSE' in market:
                market = '코스피'
            elif 'KOSDAQ' in market:
                market = '코스닥'
            else:
                market = 'err'
                logger.error('cannot find market, code={0}'.format(code))
            try:
                num_stocks = int(num_stocks.split('/')[0].replace(',', ''))
            except (ValueError, TypeError) as e:
                num_stocks = 0
                logger.error('{0} cannot find num_stocks, code={0}'.format(e, code))
        else:
            logger.error('request fail status={0}, code={1}'.format(html.status_code, code))
            market = 'err'
            num_stocks = 0
        return market, num_stocks

    def crowling_listing_date(self, code):
        logger = logs.Log().get_logger('file')
        html = requests.get(qutils.get_url(data.COMPANY_CORP_URL, code))
        if html.status_code == 200:
            bs = BeautifulSoup(html.text, 'html.parser')
            listing_date = bs.select_one('.us_table_ty1.table-hb.thbg_g.h_fix.zigbg_no ' + \
                                       'tr:nth-of-type(5) > td.l.cle').text
            try:
                listing_date = datetime.datetime.strptime(listing_date, '%Y/%m/%d')
            except (ValueError, TypeError) as e:
                logger.error('{0} cannot find listing_date, code={1}'.format(e, code))
                listing_date = datetime.date(1,1,1)
        else:
            logger.error('request fail status={0}, code={1}'.format(html.status_code, code))
            listing_date = datetime.date(1,1,1)
        return listing_date

    def check_manual_transfer(self):
        if Configurer.UPDATE_MANUAL_CHART_TRANSFER is True:
            return True
        elif Configurer.UPDATE_MANUAL_CHART_TRANSFER is False:
            return False
        else:
            raise ReferenceError("MANUAL_CHART_TRANSFER in config file must be True or False.")

    def get_chart_update_dict(self, db, update_date):
        update_list = db.get_chart_from_meta()
        update_dict = {}
        start_date = datetime.datetime.strptime(Configurer.UPDATE_START_DATE, "%Y-%m-%d").date()
        for update_row in update_list:
            code = update_row[0][2:]
            last_update = update_row[1]
            listing_date = update_row[2]
            if last_update: # update_row[1] : update_date
                latest = last_update
            elif listing_date > start_date: # update_row[2] : listing_date
                latest = listing_date
            else:
                latest = start_date
            if latest < update_date:
                update_dict[code] = {'listing':listing_date, 'last':last_update, 'latest':latest}
                # listing : company listing date
                # last : last update date
                # latest : update start date
        return update_dict

    def update_chart_tables(self, db, update_dict, update_date):
        log = logs.Log()
        log_queue = Queue()
        logger = log.config_queue_log(log_queue, name='queue')
        log.listener_start(Configurer.UPDATE_LOG_PATH, name='file', queue=log_queue)

        lock = Lock()
        buffer = Queue()

        rc = Process(target=self.receive_chart_data,
                     args=(buffer, db, len(update_dict), update_date))
        rc.start()

        tr_ohlc = Process()
        tr_investor = Process()
        while True:
            if (not tr_ohlc.is_alive()) and (tr_ohlc.exitcode != 0):
                logger.debug(f'tr_ohlc terminated with code {tr_ohlc.exitcode}')
                tr_ohlc = Process(target=self.transmit_ohlc_data,
                                  args=(buffer, update_dict, update_date, lock, log_queue, db))
                tr_ohlc.start()
            if (not tr_investor.is_alive()) and (tr_investor.exitcode != 0):
                logger.debug(f'tr_investor terminated with code {tr_investor.exitcode}')
                tr_investor = Process(target=self.transmit_investor_data,
                                      args=(buffer, update_dict, update_date, lock, log_queue))
                tr_investor.start()
            if (tr_ohlc.exitcode == 0) and (tr_investor.exitcode == 0):
                break
            time.sleep(0.1)

        log.listener_end(log_queue)
        buffer.put(None); rc.join()

        opts = ['10081', '10060']
        for opt in opts:
            file_path = Configurer.UPDATE_PICKLE_PATH + f'_{opt}.pickle'
            if isfile(file_path):
                remove(file_path)

    def receive_chart_data(self, buffer, db, update_len, update_date):
        with tqdm(total=update_len*2, ascii=True, desc='Chart Table UPDATE') as pbar:
            proc_list = defaultdict(int)
            while True:
                data = buffer.get()
                if data:
                    code, opt, df, isEnd = data
                    if opt == 10081: # ohlc data
                        for row in df.itertuples():
                            db.insert_ohlc_into_chart(code, getattr(row, 'Index'), getattr(row, 'open'),
                                                      getattr(row, 'close'), getattr(row, 'high'),
                                                      getattr(row, 'low'), getattr(row, 'volume_q'))
                    elif opt == 10060: # investor data
                        for row in df.itertuples():
                            db.insert_investor_into_chart(code, getattr(row, 'Index'), getattr(row, 'fore'),
                                                          getattr(row, 'inst'), getattr(row, 'indi'))
                    if isEnd:
                        pbar.update(1)
                        proc_list[code] += 1
                        if proc_list[code] == 2:
                            db.update_chart_date_in_meta(code, update_date)

                elif data is None:
                    break

    def transmit_ohlc_data(self, buffer, update_dict, update_date, lock, log_queue, db):
        log = logs.Log()
        logger = log.config_queue_log(log_queue, 'queue')

        app = kiwoom.QApplication(sys.argv)
        kwm = kiwoom.Kiwoom()
        self.multiproc_kiwoom_login(kwm, lock, logger)

        file_path = Configurer.UPDATE_PICKLE_PATH + '_10081.pickle'
        update_list = self.load_update_list(file_path, logger, update_dict, update_date)

        opt = 10081
        i, state, data = 0, 0, None
        for i, (code, start, end) in enumerate(update_list):
            try:
                state, data = kwm.req_opt10081(com_code=code, end_date=end,
                                                  modi_price=True, start_date=start)
            except Exception as e:
                logger.error(f"code'{code}' 10081 Error'{e}'")
                continue
            if state == -1:  # LIMIT TR COUNT
                isEnd = False
                buffer.put([code, opt, data, isEnd])
                break
            else:
                # check par value change or stock increase or decrease
                if update_dict[code]['last']:
                    before_price = db.get_recent_stock_price(code, data.index[-1])
                    after_price = data.iloc[-1]['close']
                    if before_price != after_price:  # if price is not equal at the same day
                        end = update_dict[code]['last']
                        start = datetime.datetime.strptime(Configurer.UPDATE_START_DATE, "%Y-%m-%d").date()
                        try:
                            state, data = kwm.req_opt10081(com_code=code, end_date=end,
                                                              modi_price=True, start_date=start)
                        except Exception as e:
                            logger.error(f"code'{code}' 10081 Error'{e}'")
                            continue
                        if state == -1:  # LIMIT TR COUNT
                            update_list[i:][0][1] = start
                            isEnd = False
                            buffer.put([code, opt, data, isEnd])
                            break
                isEnd = True
                buffer.put([code, opt, data, isEnd])

        exit_code = 0
        if state == -1:
            exit_code = 1
            if data:  end_date = data.index[-1]
            else:     end_date = update_date
            update_list[i:][0][2] = end_date
            with open(file_path, 'wb') as f:
                pickle.dump(update_list[i:], f)
                logger.debug('Pickle saving...')
        exit(exit_code)

    def transmit_investor_data(self, buffer, update_dict, update_date, lock, log_queue):
        log = logs.Log()
        logger = log.config_queue_log(log_queue, 'queue')

        app = kiwoom.QApplication(sys.argv)
        kwm = kiwoom.Kiwoom()
        self.multiproc_kiwoom_login(kwm, lock, logger)

        file_path = Configurer.UPDATE_PICKLE_PATH + '_10060.pickle'
        update_list = self.load_update_list(file_path, logger, update_dict, update_date)

        opt = 10060
        i, state, data = 0, 0, None
        for i, (code, start, end) in enumerate(update_list):
            try:
                state, data = kiwoom.req_opt10060(com_code=code, end_date=end, form_opt='MONEY',
                                                  trade_opt='TOTAL', start_date=start)
            except Exception as e:
                logger.error(f"code'{code}' 10060 Error'{e}'")
                continue
            if state == -1:  # LIMIT TR COUNT
                isEnd = False
                buffer.put([code, opt, data, isEnd])
                break
            else:
                isEnd = True
                buffer.put([code, opt, data, isEnd])

        exit_code = 0
        if state == -1:
            exit_code = 1
            if data:  end_date = data.index[-1]
            else:     end_date = update_date
            update_list[i:][0][2] = end_date
            with open(file_path, 'wb') as f:
                pickle.dump(update_list[i:], f)
                logger.debug('Pickle saving...')
        exit(exit_code)

    def multiproc_kiwoom_login(self, kiwoom, lock, logger):
        lock.acquire()  # process lock
        kiwoom.manual_login(user_id=Configurer.KIWOOM[0]['USER_ID'],
                            norm_pwd=Configurer.KIWOOM[0]['NORM_PWD'],
                            cert_pwd=Configurer.KIWOOM[0]['CERT_PWD'],
                            is_mock=False)
        if kiwoom.get_connect_state():
            logger.debug('Kiwoom login success.')
            lock.release()  # process unlock
        else:
            logger.debug('Kiwoom login fails, process terminated')
            lock.release()  # process unlock
            exit(1)

    def load_update_list(self, file_path, logger, update_dict, update_date):
        if isfile(file_path):
            with open(file_path, 'rb') as f:
                update_list = pickle.load(f)
                logger.debug('Pickle load...')
        else:
            update_list = [[code, update_dict[code]['latest'], update_date] for code in update_dict]
            logger.debug('Pickle file does not exist. Data gathering starts from the beginning')
        return update_list
