# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
from dateutil.parser import parse
import pickle


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
                   "코퍼스코리아","네프로아이티","수젠텍"] ## 추가필요
    ipo = ipo.drop(delete_item, axis=0)
    
    return ipo


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

# ## 시장변수

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


def MatchItem_rotation_trading(IPOcoms, FeatureDf, TargetDf, indexer, finding_1,finding_2, name, num):
    """
    트레이딩 기준 시가총액 회전율 넣어주는 공식
    """
    FeatureDf[name] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        month = parse(IPOday).date() + relativedelta(months = num)
        month = str(month)
        ## 거래대금
        money = TargetDf.loc[(i,finding_1),IPOday:month].sum(axis=1)[0]
        ## 시가총액
        mean_all = TargetDf.loc[(i,finding_2),IPOday:month].mean(axis=1)[0]
        ## 회전율
        rotation = (money/mean_all)*100
        FeatureDf.loc[i,name] = rotation
    return FeatureDf


def MatchItem_rotation_market(IPOcoms, FeatureDf, TargetDf, indexer, finding_1,finding_2, name, num):
    """
    시장 기준 시가총액 회전율 넣어주는 공식
    """
    FeatureDf[name] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        month = parse(IPOday).date() + relativedelta(months = num)
        month = str(month)
        ## 거래대금
        money = TargetDf.loc[finding_1,IPOday:month].sum()
        ## 시가총액
        mean_all = TargetDf.loc[finding_2,IPOday:month].mean()
        ## 회전율
        rotation = (money/(mean_all*1000000))*100
        FeatureDf.loc[i,name] = rotation
    return FeatureDf


def MatchItem_mean(IPOcoms, FeatureDf, TargetDf, indexer, finding , name, num):
    """
    트레이딩 변수들 1,3개월 비중 평균내는 공식
    """
    FeatureDf[name] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        month = parse(IPOday).date() + relativedelta(months = num)
        month = str(month)
        ## 변수 평균
        mean = TargetDf.loc[(i,finding),IPOday:month].mean(axis=1)[0]
        FeatureDf.loc[i,name] = mean
    return FeatureDf


def MatchItem_Market_3_6(IPOcoms, FeatureDf, TargetDf, indexer, finding , second):
    """
    Market에서 특정 변수들 3개월후 대비 1개월후 넣어주는 함수
    """
    FeatureDf[finding] = np.nan
     
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        month_3 = str((parse(IPOday) + relativedelta(months= 3)).date())
        month_1 = str((parse(IPOday) + relativedelta(months = 1)).date())
        month_v = float(TargetDf.loc[second,month_3])
        year_v = float(TargetDf.loc[second,month_1])
        per = (month_v - year_v)/year_v
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


# ## 변수 위치 재설정

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
