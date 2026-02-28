


add column 'Fee_Base' , 'Fee_Adj' , 'Fee_Class' 

then, per below, create rules, once we evaluate that, will make some regionized adjustments 

cool ?


  === ENTRANCE (INBOUND) RECORDS BY ICST VESSEL TYPE ===

                            ICST_DESC  Count Percent
                            CONTAINER  17885   21.7% = $650, class: container 
                               CRUISE   9884   12.0% = $2000, class: cruise 
                      CHEMICAL TANKER   9084   11.0% = $3750, class: parcel 
                   OTHER BULK CARRIER   8908   10.8% = $9500, class: bulk 
          TUG/SUPPLY OFFSHORE SUPPORT   7154    8.7% = $0, filter
                    OTHER RO-RO CARGO   6702    8.1% = $750, class: ro-ro 
         GENERAL CARGO-MULTI DECK NEI   5110    6.2% = $4500, class: general cargo 
                     CRUDE OIL TANKER   3448    4.2% = $4500, class: general cargo 
                          LPG CARRIER   3285    4.0% = $3750, class: lpg
                                  TUG   1629    2.0% = $0, filter 
                          LNG CARRIER   1472    1.8% = $4500, class: lng 
                         OTHER LAKERS   1186    1.4% = $0, filter ONLY US, CA flag, others $5750, class: bulk 
                CRUDE/PRODUCTS TANKER   1107    1.3% = $3750, class: tank
        OTHER SPECIALIZED CARRIER NEI    672    0.8% = $4500, class: general 
                  OIL PRODUCTS TANKER    665    0.8% = $4000, class: tank
                     OTHER TANK BARGE    505    0.6% = $0, filter 
                               REEFER    437    0.5% = $4500, class: reefer
                            PUSH BOAT    418    0.5% = $0, filter
                      RO-RO PASSENGER    412    0.5% = $0, filter 
            OTHER DRY CARGO BARGE NEI    381    0.5% = $0, filter 
                           DECK BARGE    381    0.5% = $0, filter 
                         OTHER TANKER    346    0.4% = $4000, class: tank 
                      DRY CARGO BARGE    295    0.4% = $0, filter 
                      RESEARCH/SURVEY    249    0.3% = $0, filter 
                      RO-RO CONTAINER    157    0.2% = $750, class: ro-ro
          OTHER LIQUIFIED GAS CARRIER     88    0.1% = $4500, class: lpg  
                     OTHER TANKER NEI     86    0.1% = $3750, class: tank
              COVERED DRY CARGO BARGE     85    0.1% = $0, filter 
                        FISH CATCHING     74    0.1% = $0, filter 
                            OTHER NEI     74    0.1% = $0, filter 
  OTHER OFFSHORE PRODUCTION & SUPPORT     44    0.1% = $0, filter 
                      FISH PROCESSING     29    0.0% = $0, filter 
                      OTHER PASSENGER     28    0.0% = $0, filter 
               OTHER BULK/OIL CARRIER     27    0.0% = $9500, class: bulk 
                  OTHER GENERAL CARGO     13    0.0% = $4500, class: general 
                    LIVESTOCK CARRIER     11    0.0% = $4500, class: general 
                        DRILLING SHIP     10    0.0% = $0, filter 
                              DREDGER      1    0.0% = $0, filter 
                      VEHICLE CARRIER      1    0.0% = $0, filter

  Total Records: 82,343