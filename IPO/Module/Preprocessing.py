# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
from dateutil.parser import parse
import pickle


# +
def ipo_processing(ipo):
    """
    ipo 엑셀파일 전처리
    """
    ipo = ipo[['상장유형','종목명','공모가','상장일','상장주식수','경쟁률']] ## 필요한 열만 사용
    ipo = ipo[~ipo['종목명'].str.contains("스팩")] ## 스팩이 들어간 종목 제거 92개
    ipo.set_index('종목명',inplace = True) ## 종목명을 인덱스로 설정
    
#     ipo['상장일'] = pd.to_datetime(ipo['상장일']) ## 날짜 계산을 위해 dt변환
#     ipo = ipo[ipo['상장일'] < '2020-12-31'] ## 상장일 이후 3개월 안되는 종목 삭제757개 -> 689개
#     ipo = ipo[ipo['상장유형'] != '상장'] ## 재상장은 공모가가 0원으로 잡힘 689개 -> 665개
    ipo['상장일'] = ipo['상장일'].astype(str) ## 추후 인덱싱을 위한 str처리
    
    ## 데이터 값 전부 없는 경우 삭제
    delete_item = ["성융광전투자유한공사","리드",
                   "로보티즈","원바이오젠",
                   "코퍼스코리아","수젠텍","강원","녹십자랩셀","펌텍코리아","포커스에이치엔에스"] ## 추가필요
    ipo = ipo.drop(delete_item, axis=0)
    
    return ipo


# -

def FeatureDf_processing(FeatureDf):
    """
    IPO 파일에 넣어줄 변수가 있는 엑셀 전처리
    """
    # 데이터 삭제를 위한 종목명으로 인덱스 설정
    FeatureDf.set_index(["Name","Item"],inplace= True)

    return FeatureDf


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



# -

# ## 트레이딩 변수

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

def MatchItem_per(IPOcoms, FeatureDf, finding ,num):
    """
    per/pbr/ev 등등 구하기
    """
    FeatureDf[finding] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        month = str(parse(IPOday).date() + relativedelta(months=num))
        
        if parse(month).date().month < 4:
            day= datetime(parse(month).year,12,31).date() - \
            relativedelta(years = 2)
        else :
            day = datetime(parse(month).year,12,31).date() - \
            relativedelta(years = 1)
            
        num_1 = trading.loc[(i,'종가'),month]
        num_2 = stock.loc[i,month][0]
        num_3 = finance.loc[(i,'당기순이익'),str(day)]
        
        per = (num_1*num_2)/(num_3*1000)
        FeatureDf.loc[i,finding] = per
    return FeatureDf


def MatchItem_pbr(IPOcoms, FeatureDf, finding ,num):
    """
    per/pbr/ev 등등 구하기
    """
    FeatureDf[finding] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        month = str(parse(IPOday).date() + relativedelta(months=num))
        
        if parse(month).date().month < 4:
            day= datetime(parse(month).year,12,31).date() - \
            relativedelta(years = 2)
        else :
            day = datetime(parse(month).year,12,31).date() - \
            relativedelta(years = 1)
            
        num_1 = trading.loc[(i,'종가'),month]
        num_2 = stock.loc[i,month][0]
        num_3 = finance.loc[(i,'자본총계'),str(day)]
        
        pbr = (num_1*num_2)/(num_3*1000)
        FeatureDf.loc[i,finding] = pbr
    return FeatureDf


def MatchItem_ev(IPOcoms, FeatureDf, finding ,num):
    """
    per/pbr/ev 등등 구하기
    """
    FeatureDf[finding] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        month = str(parse(IPOday).date() + relativedelta(months=num))
        
        if parse(month).date().month < 4:
            day= datetime(parse(month).year,12,31).date() - \
            relativedelta(years = 2)
        else :
            day = datetime(parse(month).year,12,31).date() - \
            relativedelta(years = 1)
            
        num_1 = trading.loc[(i,'종가'),month]
        num_2 = stock.loc[i,month][0]
        num_3 = finance.loc[(i,'순부채'),str(day)]
        num_4 = finance.loc[(i,'EBITDA2'),str(day)]
        
        ebitda = (num_1*num_2 + num_3*1000)/(num_4*1000)
        FeatureDf.loc[i,finding] = ebitda
    return FeatureDf


def MatchItem_mean(IPOcoms, FeatureDf, TargetDf, indexer, finding , name, num):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
    """
    FeatureDf[name] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        month = parse(IPOday).date() + relativedelta(months = num)
        month = str(month)
        ## 변수 평균
        mean = TargetDf.loc[(i,finding),IPOday:month].mean()
        FeatureDf.loc[i,name] = mean
    return FeatureDf



def MatchItem_rotation(IPOcoms, FeatureDf, TargetDf, indexer, finding_1,finding_2, name, num):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
    """
    FeatureDf[name] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        month = parse(IPOday).date() + relativedelta(months = num)
        month = str(month)
        ## 거래대금
        money = TargetDf.loc[(i,finding_1),IPOday:month].sum()
        ## 시가총액
        mean_all = TargetDf.loc[(i,finding_2),IPOday:month].mean()
        ## 회전율
        rotation = (money/mean_all)*100
        FeatureDf.loc[i,name] = rotation
    return FeatureDf


def MatchItem_month(IPOcoms, FeatureDf, TargetDf, indexer, finding , month_index , month ):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
    """
    IPOcoms = FeatureDf.index
    FeatureDf[month_index + '' + finding] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        date = parse(IPOday)
        newday = date.date() + relativedelta(months=month)
        Adj_price = TargetDf.loc[(i,finding),str(newday)]
        FeatureDf.loc[i,month_index + '' + finding] = Adj_price
    return FeatureDf


# ## 시장변수

def MatchItem_marketmoney(IPOcoms, FeatureDf, TargetDf, name):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
    """
    FeatureDf[name] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        day_1 = str(parse(IPOday).date() - relativedelta(years = 1))
        day_2 = str(parse(IPOday).date() - relativedelta(months = 1))
        ## 거래대금
        money = TargetDf.loc['거래대금',day_1:day_2].sum()
        ## 시가총액
        mean_all = TargetDf.loc['시가총액',day_1:day_2].mean()
        ## 회전율
        rotation = (money/mean_all)*100
        FeatureDf.loc[i,name] = rotation
    return FeatureDf


def MatchItem_marketmoney_ipo(IPOcoms, FeatureDf, TargetDf, name,num):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
    """
    FeatureDf[name] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        day_1 = str(parse(IPOday).date() + relativedelta(months = num))
        ## 거래대금
        money = TargetDf.loc['거래대금',IPOday:day_1].sum()
        ## 시가총액
        mean_all = TargetDf.loc['시가총액',IPOday:day_1].mean()
        ## 회전율
        rotation = (money/mean_all)*100
        FeatureDf.loc[i,name] = rotation
    return FeatureDf


def MatchItem_Market_1_3(IPOcoms, FeatureDf, TargetDf, finding , second):
    """
    Market에서 특정 변수들 1년전 대비 1달 전 가격 넣어주는 함수
    """
    FeatureDf[finding] = np.nan
     
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        year = str((parse(IPOday) - relativedelta(years= 1)).date())
        month = str((parse(IPOday) - relativedelta(months = 1)).date())
        month_v = float(TargetDf.loc[second,month])
        year_v = float(TargetDf.loc[second,year])
        per = (month_v - year_v)/year_v
        FeatureDf.loc[i,finding] = per
    return FeatureDf


def MatchItem_Market_ipo(IPOcoms, FeatureDf, TargetDf, finding , standard,num):
    """
    Market에서 특정 변수들 상장일 대비 몇개월후 넣어주는 함수
    """
    FeatureDf[finding] = np.nan
     
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        month = str((parse(IPOday) + relativedelta(months=num)).date())

        month_v = float(TargetDf.loc[standard,month])
        year_v = float(TargetDf.loc[standard,IPOday])
        per = (month_v - year_v)/year_v
        FeatureDf.loc[i,finding] = per
    return FeatureDf


def MatchItem_interest(IPOcoms, FeatureDf, TargetDf,finding , standard):
    """
    상장일 기준 국고3년금리
    """
    FeatureDf[finding] = np.nan
     
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        per =  TargetDf.loc[standard,str(IPOday)]
       
        FeatureDf.loc[i,finding] = per
    return FeatureDf


# ## 종속변수

def return_rate(IPOcoms,FeatureDf,TargetDf,name,num):
    """
    공모가 대비 1,3,6 수익률 계산
    """
    
    FeatureDf[name] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        month = parse(IPOday).date() + relativedelta(months = num)
        month = str(month)
        ## 몇 개월 뒤 종가
        new_price = TargetDf.loc[(i,'종가'),month]
        ## 공모가
        pre_price = FeatureDf.loc[i,'공모가']
        ## 수익률
        return_rate = (new_price - pre_price)/pre_price
        FeatureDf.loc[i,name] = return_rate
    return FeatureDf


def rate_month_to_month(IPOcoms, FeatureDf, TargetDf, name, num_first, num_second):
    """
    1_3 수익률 , 3_6 수익률 계산
    """
    FeatureDf[name] = np.nan
     
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,'상장일']
        first_m = str(parse(IPOday).date() + relativedelta(months = num_first))
        second_m = str(parse(IPOday).date() + relativedelta(months = num_second))
        ## 첫번째 개월 뒤 종가
        new_price = TargetDf.loc[(i,'종가'),first_m]
        ## 두번째 개월 뒤 종가
        next_price = TargetDf.loc[(i,'종가'),second_m]
        
        ## 수익률
        return_rate = (new_price - next_price)/next_price
        FeatureDf.loc[i,name] = return_rate
                       
                       
    return FeatureDf


def scoring(x):
    """
    카테고리화 예시
    """
    if x <  -0.40:
        return 1
    elif x < -0.20:
        return 2
    elif x < 0 :
        return 3
    elif x < 0.20:
        return 4
    else :
        return 5

def calUp(Series):
    deltas = [0]
    for i in range(len(Series)-1):
        delta = (Series[i+1] - Series[i]) / Series[i]
        deltas.append(delta)
    return deltas
    
def CutSize(df, col):
    # 일단 3등분만 할 것 같아서 이렇게 만듬. 여러개면 switch 함수를 따로 만들고 리스트로 quantile 받기
    Cuts = []
    Cuts.append(df[col].quantile(0)-1)
    Cuts.append(df[col].quantile(0.3))
    Cuts.append(df[col].quantile(0.7))
    Cuts.append(df[col].quantile(1)+1)
    labels = [1,2,3]
    return pd.cut(df[col],Cuts, labels = labels)

# ## 변수 위치 재설정

"""
test = test[['상장유형',
 '공모가(원)',
 '상장일',
 '상장주식수',
 'IPO시가총액',
 '매출총이익률',
 '영업이익률',
 'ROE(지배)',
 '매출액증가율(YoY)',
 '영업이익증가율(YoY)',
 '매출액증가율(YoY)-before',
 '영업이익증가율(YoY)-before',
 '유동비율',
 '당좌비율',
 '부채비율',
 '이자보상배율',
 '매출채권회전율',
 '재고자산회전율',
 '매출액',
 '세전계속사업이익',
 '당기순이익(지배)',
 '자본총계(지배)',
 'EBITDA2',
 '순부채',
 'IPO_PER',
 'IPO_PBR',
 'IPO_EV/EBIDTA',
 'IPO_PSR',
 '1개월 시가총액회전율',
 '3개월 시가총액회전율',
 '1개월 평균 거래량회전율',
 '3개월 평균 거래량회전율',
 '1개월 평균 일중변동률',
 '3개월 평균 일중변동률',
 '1개월 평균 개인 매도수량 비중(일간)',
 '3개월 평균 개인 매도수량 비중(일간)',
 '1개월 평균 개인 매수수량 비중(일간)',
 '3개월 평균 개인 매수수량 비중(일간)',
 '1개월 평균 기관 매수수량 비중(일간)',
 '3개월 평균 기관 매수수량 비중(일간)',
 '1개월 평균 기관 매도수량 비중(일간)',
 '3개월 평균 기관 매도수량 비중(일간)',
 '시장수익률',
'1개월 시장 회전율',
 '3개월 시장 회전율',
 'M2 증감률 ',
 'MMF 증감률 ',
 '고객예탁금 증감률 ',
 '국고1년시장금리%p',
 '국고3년시장금리%p',
 '국고5년시장금리%p']]

## 멀티인덱스 설정
test.columns = [['IPO']*5 + ['Finance']*23 + ['Trading']*14 + ['Market']*9 ,\
['IPO지표']*5 + ['수익성']*3 + ['성장성']*4 + ['유동성']*2 + ['안정성']*2 + \
['활동성']*2 +['규모']*2 + ['삭제할듯']*4 + ['가격결정자 정보']*4 + ['유동지표'] \
*6 +['매매비중정보']*8 + ['코스닥정보']*3 + ['유동성']*3 +['금리']*3 ,\
['상장유형',
 '공모가(원)',
 '상장일',
 '상장주식수',
 'IPO시가총액',
 '매출총이익률',
 '영업이익률',
 'ROE(지배)',
 '매출액증가율(YoY)',
 '영업이익증가율(YoY)',
 '매출액증가율(YoY)-before',
 '영업이익증가율(YoY)-before',
 '유동비율',
 '당좌비율',
 '부채비율',
 '이자보상배율',
 '매출채권회전율',
 '재고자산회전율',
 '매출액',
 '세전계속사업이익',
 '당기순이익(지배)',
 '자본총계(지배)',
 'EBITDA2',
 '순부채',
 'IPO_PER',
 'IPO_PBR',
 'IPO_EV/EBIDTA',
 'IPO_PSR',
 '1개월 시가총액회전율',
 '3개월 시가총액회전율',
 '1개월 평균 거래량회전율',
 '3개월 평균 거래량회전율',
 '1개월 평균 일중변동률',
 '3개월 평균 일중변동률',
 '1개월 평균 개인 매도수량 비중(일간)',
 '3개월 평균 개인 매도수량 비중(일간)',
 '1개월 평균 개인 매수수량 비중(일간)',
 '3개월 평균 개인 매수수량 비중(일간)',
 '1개월 평균 기관 매수수량 비중(일간)',
 '3개월 평균 기관 매수수량 비중(일간)',
 '1개월 평균 기관 매도수량 비중(일간)',
 '3개월 평균 기관 매도수량 비중(일간)',
 '시장수익률',
'1개월 시장 회전율',
 '3개월 시장 회전율',
 'M2 증감률 ',
 'MMF 증감률 ',
 '고객예탁금 증감률 ',
 '국고1년시장금리%p',
 '국고3년시장금리%p',
 '국고5년시장금리%p']]

# > 엑셀 불러오면 멀티인덱스 풀리기에 불러온 뒤 멀티인덱스 편하게 설정하는 방법 찾기
"""