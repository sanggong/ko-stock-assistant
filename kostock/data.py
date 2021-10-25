HOLIDAY_URL = "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo"
WICS_URL = "http://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt={}&sec_cd=G{}"  # date, wics code
COMPANY_MAIN_URL = "https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A{}&cID=&MenuYn=Y&ReportGB=&NewMenuID=Y&stkGb=701"  # stock code
COMPANY_CORP_URL = "https://comp.fnguide.com/SVO2/ASP/SVD_Corp.asp?pGB=1&gicode=A{}&cID=&MenuYn=Y&ReportGB=&NewMenuID=Y&stkGb=701"  # stock code

WICS_LC = {10: '에너지',
           15: '소재',
           20: '산업재',
           25: '경기관련소비재',
           30: '필수소비재',
           35: '건강관리',
           40: '금융',
           45: 'IT',
           50: '커뮤니케이션서비스',
           55: '유틸리티'}

WICS_MC = {1010: '에너지',
           1510: '소재',
           2010: '자본재',
           2020: '상업서비스와공급품',
           2030: '운송',
           2510: '자동차와부품',
           2520: '내구소비재와의류',
           2530: '호텔,레스토랑,레저 등',
           2550: '소매(유통)',
           2560: '교육서비스',
           3010: '식품과기본식료품소매',
           3020: '식품,음료,담배',
           3030: '가정용품과개인용품',
           3510: '건강관리장비와서비스',
           3520: '제약과생물공학',
           4010: '은행',
           4020: '증권',
           4030: '다각화된금융',
           4040: '보험',
           4050: '부동산',
           4510: '소프트웨어와서비스',
           4520: '기술하드웨어와장비',
           4530: '반도체와반도체장비',
           4535: '전자와 전기제품',
           4540: '디스플레이',
           5010: '전기통신서비스',
           5020: '미디어와엔터테인먼트',
           5510: '유틸리티'}