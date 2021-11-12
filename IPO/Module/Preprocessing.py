# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
from dateutil.parser import parse


# +
# ipo = KQ_IPO
# finance = KQ_Finance
# trading = KQ_Trading
# -

def ipo_processing(ipo):
    """
    ipo 엑셀파일 전처리
    """
    ipo = ipo[['상장유형','종목명','공모가(원)','상장일','상장주식수']] ## 필요한 열만 사용
    ipo = ipo[~ipo['종목명'].str.contains("스팩")] ## 스팩이 들어간 종목 제거
    ipo.set_index('종목명',inplace = True) ## 종목명을 인덱스로 설정
    
    ipo['상장일'] = pd.to_datetime(ipo['상장일']) ## 날짜 계산을 위해 dt변환
    ipo = ipo[ipo['상장일'] < '2019-06-30'] ## 상장일 이후 6개월 안되는 종목 삭제757개 -> 689개
    ipo = ipo[ipo['상장유형'] != '재상장'] ## 재상장은 공모가가 0원으로 잡힘 689개 -> 665개
    ipo['상장일'] = ipo['상장일'].astype(str) ## 추후 인덱싱을 위한 str처리
    
    ## 데이터 값 전부 없는 경우 삭제
    delete_item = ["성융광전투자유한공사","리드","케이엠에이치신라레저",
                   "펩트론","파마리서치","신텍","로보티즈","원바이오젠",
                   "코퍼스코리아"] ## 추가필요
    ipo = ipo.drop(delete_item, axis=0)
    
    return ipo
ipo = ipo_processing(ipo)


# +
def FeatureDf_processing(FeatureDf):
    """
    IPO 파일에 넣어줄 변수가 있는 엑셀 전처리
    """
    # 데이터 삭제를 위한 종목명으로 인덱스 설정
    FeatureDf.set_index(["Name","Item"],inplace= True)

     return FeatureDf

finance = FeatureDf_processing(finance)
trading = FeatureDf_processing(trading)


# -

# ## 파이낸스 변수 추가

# +
def MatchItem_finance(IPOcoms, FeatureDf, TargetDf, indexer, finding):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 
    TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
    4월 이전 상장한 것들은 2년 전 정보, 이후는 1년 전 정보 가져오기
    """
    FeatureDf[finding] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        if parse(IPOday).date().month < 4:
            IPOday= datetime(parse(IPOday).year,12,31).date()\
            -relativedelta(years = 2)
        else :
            IPOday= datetime(parse(IPOday).year,12,31).date()\
            - relativedelta(years = 1)
        Adj_price = TargetDf.loc[(i,finding),str(IPOday)]
        FeatureDf.loc[i,finding] = Adj_price[0]
    return FeatureDf

def Matchitem_New(FeatureDF):
    """
    finance에 있는 변수마다 ipo 파일 옆에 붙여주기
    
    """
    IPOcoms = ipo.index
    New_coms = FeatureDF.reset_index(drop = False , inplace = False)
    New_coms = list(New_coms['Item'].dropna().unique())
    for i in New_coms:
        Train_data = MatchItem_finance(IPOcoms,ipo,FeatureDF,'상장일',i) ## 
    return Train_data

Train_data = Matchitem_New(finance)


# +
def new_fi(IPOcoms,FeatureDf, TargetDf, indexer, finding):
    FeatureDf[finding + '-before'] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        if parse(IPOday).date().month < 4:
            IPOday= datetime(parse(IPOday).year,12,31).date()\
            - relativedelta(years = 3)
        else :
            IPOday= datetime(parse(IPOday).year,12,31).date()\
            - relativedelta(years = 2)
        Adj_price = TargetDf.loc[(i,finding),str(IPOday)]
        FeatureDf.loc[i,finding + '-before'] = Adj_price[0]
    return FeatureDf

IPOcoms = ipo.index
Train_data = new_fi(IPOcoms,Train_data,finance,'상장일','매출액증가율(YoY)')
Train_data = new_fi(IPOcoms,Train_data,finance,'상장일','영업이익증가율(YoY)')
# -

Train_data.to_csv("X_train(finance).csv",encoding = 'euc-kr')
## 파이낸스 정보만 들어간 것

# ## 트레이딩 변수

test = Train_data.copy()

## IPO_Per 계산 공식
test['IPO_PER'] = test['공모가(원)']/(test['당기순이익(지배)']*1000/test['상장주식수'])
## IPO_Pbr
test['IPO_PBR'] = test['공모가(원)']/(test['자본총계(지배)']*1000/test['상장주식수'])
## IPO_EV/EBIDTA
test['IPO_EV/EBIDTA'] = ((test['공모가(원)']*test['상장주식수'])+test['순부채'])/(test['EBITDA2']*1000)
## IPO_PSR
test['IPO_PSR'] = test['공모가(원)']/(test['매출액']*1000/test['상장주식수'])


def MatchItem(IPOcoms, FeatureDf, TargetDf, indexer, finding):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
    상장일에 해당하는 stock 변수 넣음
    """
    FeatureDf[finding] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        Adj_price = TargetDf.loc[(i,finding),IPOday]
        FeatureDf.loc[i,finding] = Adj_price
    return FeatureDf



# +
def MatchItem_month(IPOcoms, FeatureDf, TargetDf, indexer, finding , month_index , month ):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
    상장 후 1달,3달,6달 후 수정주가 넣음
    """
    IPOcoms = FeatureDf.index
    FeatureDf[month_index + ' ' + finding] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        date = parse(IPOday)
        newday = date.date() + relativedelta(months=month)
        Adj_price = TargetDf.loc[(i,finding),str(newday)]
        FeatureDf.loc[i,month_index + ' ' + finding] = Adj_price
    return FeatureDf

# Traindata = MatchItem_month(IPOcoms,Traindata,stock,'상장일','수정고가','1달 후',1)


# -

# ## 시장변수

# market = KQ_Market
market.set_index('Item Name ', inplace = True)


def MatchItem_Market_1_3(IPOcoms, FeatureDf, TargetDf, indexer, finding , second):
    """
    Market에서 특정 변수들 1년전 대비 1달 전 가격 넣어주는 함수
    """
    FeatureDf[finding] = np.nan
     
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        year = str((parse(IPOday) - relativedelta(years= 1)).date())
        month = str((parse(IPOday) - relativedelta(months = 1)).date())
        month_v = float(TargetDf.loc[second,month])
        year_v = float(TargetDf.loc[second,year])
        per = (month_v - year_v)/year_v
        FeatureDf.loc[i,finding] = per
    return FeatureDf


test = MatchItem_Market_1_3(IPOcoms, test, market, \
                            '상장일', '시장수익률' , '종가지수')
test = MatchItem_Market_1_3(IPOcoms, test , market,\
                            '상장일', 'M2 증감률 ' , 'M2')
test = MatchItem_Market_1_3(IPOcoms, test , market,\
                            '상장일', 'MMF 증감률 ' , 'MMF')
test = MatchItem_Market_1_3(IPOcoms, test , market,\
                            '상장일', '고객예탁금 증감률 ' , '고객예탁금')


def MatchItem_interest_1_3(IPOcoms, FeatureDf, TargetDf, indexer, finding , second):
    """
    Market에서 금리변수들 1년전 대비 1달 전 가격 넣어주는 함수
    """
    FeatureDf[finding] = np.nan
     
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        year = str((parse(IPOday) - relativedelta(years= 1)).date())
        month = str((parse(IPOday) - relativedelta(months = 1)).date())
        month_v = float(TargetDf.loc[second,month])
        year_v = float(TargetDf.loc[second,year])
        per = month_v - year_v
        FeatureDf.loc[i,finding] = per
    return FeatureDf


test = MatchItem_interest_1_3(IPOcoms, test, market,\
                              '상장일','국고1년시장금리%p' , '국고1년시장금리')
test = MatchItem_interest_1_3(IPOcoms, test, market,\
                              '상장일', '국고3년시장금리%p' , '국고3년시장금리')
test = MatchItem_interest_1_3(IPOcoms, test, market,\
                              '상장일', '국고5년시장금리%p' , '국고5년시장금리')

test.to_csv("X_train_1_3.csv",encoding = 'euc-kr')
## 위의 트레이딩 + market변수 추가
