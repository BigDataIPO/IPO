# -*- coding: utf-8 -*-
def ipo_processing(ipo):
    """
    ipo 엑셀파일 전처리
    """
    ipo = ipo[['상장유형','시장구분','종목명','공모가(원)','상장일']] ## 필요한 열만 사용
    ipo = ipo[~ipo['종목명'].str.contains("스팩")] ## 스팩이 들어간 종목 제거
    ipo.set_index('종목명',inplace = True) ## 종목명을 인덱스로 설정
    
    ipo['상장일'] = pd.to_datetime(ipo['상장일']) ## 날짜 계산을 위해 dt변환
    ipo = ipo[ipo['상장일'] < '2019-06-30'] ## 상장일 이후 6개월 안되는 종목 삭제757개 -> 689개
    ipo = ipo[ipo['상장유형'] != '재상장'] ## 재상장은 공모가가 0원으로 잡힘 689개 -> 665개
    ipo['상장일'] = ipo['상장일'].astype(str) ## 추후 인덱싱을 위한 str처리
    
    ## 데이터 값 전부 없는 경우 삭제
    delete_item = ["성융광전투자유한공사","리드","케이엠에이치신라레저","펩트론","파마리서치","신텍"]
    ipo = ipo.drop(delete_item, axis=0)
    
    return ipo
#ipo = ipo_processing(ipo)


# +
def FeatureDf_processing(FeatureDf):
    """
    IPO 파일에 넣어줄 변수가 있는 엑셀 전처리
    """
    # 데이터 삭제를 위한 종목명으로 인덱스 설정
    FeatureDf.set_index("Name",inplace= True)

    # 데이터 값 전부 없는 경우 삭제
    delete_item = ["성융광전투자유한공사","리드","케이엠에이치신라레저","펩트론","파마리서치","신텍"]
    FeatureDf = FeatureDf.drop(delete_item, axis=0)
    
    # 멀티인덱스 재조정
    FeatureDf.set_index("Item",inplace= True,append = True)
    
    return FeatureDf

# stock = FeatureDf_processing(stock)
# trading = FeatureDf_processing(trading)


# +
def MatchItem(IPOcoms, FeatureDf, TargetDf, indexer, finding):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
    """
    FeatureDf[indexer + finding] = np.nan
    for i in IPOcoms:
        IPOday = FeatureDf.loc[i,indexer]
        Adj_price = TargetDf.loc[(i,finding),IPOday]
        FeatureDf.loc[i,indexer + finding] = Adj_price[0]
    return FeatureDf

#Traindata = MatchItem(IPOcoms,ipo,stock,'상장일','수정주가')


# +
def MatchItem_month(IPOcoms, FeatureDf, TargetDf, indexer, finding , month_index , month ):
    """
    IPO상장기업에 대해서 특정날(indexer)에 찾고자하는 지표(finding)을 TargetDf에서 찾은뒤 FeatureDf에 indexer날에 넣어줌
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


# +
New_com = trading.loc['메디톡스'].index ## 새로운 컬럼이 있는 df 이름이 trading 경우

def Matchitem_New(New_coms, FeatureDF):
    """
    IPO종목에 대한 새로운 컬럼 가져왔을때 Clean_data에 추가로 열 생성
    """
    New_coms = FeatureDF.loc['메디톡스'].index
    for i in New_coms:
        Train_data = MatchItem(IPOcoms,Traindata,FeatureDF,'상장일',i)
        
    return Train_data
# Train_data = Matchitem_New(New_com, trading)
