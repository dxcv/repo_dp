/*
Created on Tue Jan 17 11:00:00 2017      
@author: Fernando Suarez      
Consulta para mapear la cartera de los distintos portfolios a sus respectivs indices representativos, la consulta se subdivide en cuatro uniones: 
- depositos, bonos y acciones  
- forward de moneda long leg  
- forward de moneda short leg  
- cajas en distintas monedas para fondos mutuos  
- cajas en distintas monedas para fondos de inversion  
*/ 
-- La consulta primero computa el mapeo de los instrumentos de la cartera ex derivados ex caja
SELECT Ltrim(Rtrim(zc.fecha))                               AS fecha, 
       Ltrim(Rtrim(zc.codigo_fdo)) COLLATE database_default AS codigo_fdo, 
       Ltrim(Rtrim(zc.codigo_emi)) COLLATE database_default AS codigo_emi, 
       Ltrim(Rtrim(zc.codigo_ins)) COLLATE database_default AS codigo_ins, 
       Ltrim(Rtrim(zc.tipo_instrumento))                    AS tipo_instrumento, 
       Ltrim(Rtrim(zc.moneda)) COLLATE database_default     AS moneda, 
       Cast(zc.monto AS FLOAT)                              AS monto, 
       Cast(zc.nominal AS FLOAT)                            AS nominal, 
       Cast(zc.cantidad AS FLOAT)                           AS cantidad, 
       Cast(zc.precio AS FLOAT)                             AS precio, 
       Cast(zc.duration AS FLOAT)                           AS duration, 
       Cast(zc.tasa/100 AS FLOAT)                           AS tasa, 
       Ltrim(Rtrim(zc.riesgo))                              AS riesgo, 
       Ltrim(Rtrim(zc.nombre_emisor))                       AS nombre_emisor, 
       Ltrim(Rtrim(zc.nombre_instrumento))                  AS 
       nombre_instrumento, 
       Ltrim(Rtrim(zc.fec_vcto))                            AS fec_vtco, 
       Ltrim(Rtrim(zc.pais_emisor))                         AS pais_emisor, 
       -- Aca empieza el mapeo de los instrumentos a indices representativos    
       CASE 
         WHEN zc.tipo_instrumento = 'Bono de Gobierno' THEN 
           -- Mapping soberanos    
           --BONOS SOBERANOS          
           CASE 
             WHEN zc.moneda = '$' THEN 
               CASE 
                 WHEN zc.duration BETWEEN 0.0 AND 2.5 THEN 128 
                 WHEN zc.duration BETWEEN 2.5 AND 3.5 THEN 129 
                 WHEN zc.duration BETWEEN 3.5 AND 4.5 THEN 130 
                 WHEN zc.duration BETWEEN 4.5 AND 5.92 THEN 131 
                 WHEN zc.duration BETWEEN 5.92 AND 7.92 THEN 132 
                 WHEN zc.duration BETWEEN 7.92 AND 10.92 THEN 134--Este borramos el original y hay que reemplazarlo
                 WHEN zc.duration BETWEEN 10.92 AND 20.0 THEN 134 
                 WHEN zc.duration BETWEEN 20.0 AND 30.0 THEN 135
               END 
             WHEN zc.moneda = 'UF' THEN 
               CASE 
                 WHEN zc.duration BETWEEN 0.0 AND 2.5 THEN 136 
                 WHEN zc.duration BETWEEN 2.5 AND 3.5 THEN 137 
                 WHEN zc.duration BETWEEN 3.5 AND 4.5 THEN 138 
                 WHEN zc.duration BETWEEN 4.5 AND 5.92 THEN 139 
                 WHEN zc.duration BETWEEN 5.92 AND 7.92 THEN 140 
                 WHEN zc.duration BETWEEN 7.92 AND 10.92 THEN 141 
                 WHEN zc.duration BETWEEN 10.92 AND 20.0 THEN 142 
                 WHEN zc.duration BETWEEN 20.0 AND 30.0 THEN 143 
               END 
             WHEN zc.moneda = 'US$' THEN 
               CASE 
                 WHEN zc.pais_emisor IN ( 'US' ) THEN 62 
                 --Esto le agrega mas volatilidad al MMARKET 
                 WHEN zc.pais_emisor IN ( 'BR', 'MX', 'PE', 'CL', 'CO' ) THEN 
                 167 
               END 
             WHEN zc.moneda = 'EU' THEN 73
             WHEN zc.moneda = 'ARS' THEN 593
             WHEN zc.moneda = 'REA' THEN
                  CASE 
                    WHEN zc.codigo_ins = 'BRASIL0127'  THEN 485
                 END
             WHEN zc.moneda = 'MX' THEN 
                 CASE 
                    WHEN zc.codigo_ins = 'MBONO 0529'  THEN 462
                    WHEN zc.codigo_ins in ('MBONO 0621', 'MBONO0621')  THEN 463
                    WHEN zc.codigo_ins = 'MBONO 1136'  THEN 464
                    WHEN zc.codigo_ins = 'MBONO 1224'  THEN 465
                    WHEN zc.codigo_ins = 'MBONO05/31'  THEN 466
                    WHEN zc.codigo_ins in ('MBONO 1142', 'MBONO11/42')  THEN 467
                 END
            WHEN zc.moneda = 'SOL' THEN
                 CASE 
                    WHEN zc.codigo_ins = 'PERU'  THEN 627
                 END
          END 
         WHEN zc.tipo_instrumento = 'Bono Corporativo' THEN -- Mapping Spread    
           CASE 
             WHEN zc.moneda = '$' THEN 
               CASE 
                 WHEN zc.riesgo IN ( 'AAA' ) THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND 1.0 THEN 145 
                     WHEN zc.duration BETWEEN 1.0 AND 3.0 THEN 106 
                     WHEN zc.duration BETWEEN 3.0 AND 5.0 THEN 109 
                     WHEN zc.duration BETWEEN 5.0 AND 30.0 THEN 111 
                   END 
                 WHEN zc.riesgo IN ( 'AA+', 'AA', 'AA-' ) THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND 1.0 THEN 104 
                     WHEN zc.duration BETWEEN 1.0 AND 3.0 THEN 107 
                     WHEN zc.duration BETWEEN 3.0 AND 5.0 THEN 110 
                     WHEN zc.duration BETWEEN 5.0 AND 30.0 THEN 112 
                   END 
                 WHEN zc.riesgo IN ( 'A+', 'A', 'A-' ) THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND 2.0 THEN 87 
                     WHEN zc.duration BETWEEN 2.0 AND 3.0 THEN 88 
                     WHEN zc.duration BETWEEN 3.0 AND 5.0 THEN 89 
                     WHEN zc.duration BETWEEN 5.0 AND 7.0 THEN 90 
                     WHEN zc.duration BETWEEN 7.0 AND 30.0 THEN 91 
                   END 
                 WHEN zc.riesgo IN ( 'BBB+', 'BBB', 'BBB-', 'BB+', 
                                     'BB', 'BB-', 'B+', 'B', 
                                     'B-', 'C' ) THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND 2.0 THEN 123 
                     WHEN zc.duration BETWEEN 2.0 AND 3.0 THEN 124 
                     WHEN zc.duration BETWEEN 3.0 AND 5.0 THEN 125 
                     WHEN zc.duration BETWEEN 5.0 AND 7.0 THEN 126 
                     WHEN zc.duration BETWEEN 7.0 AND 150.0 THEN 127 
                   END 
               END 
             WHEN zc.moneda = 'UF' THEN 
               CASE 
                 WHEN zc.riesgo IN ( 'AAA' ) THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND 1.0 THEN 92 
                     WHEN zc.duration BETWEEN 1.0 AND 3.0 THEN 95 
                     WHEN zc.duration BETWEEN 3.0 AND 5.0 THEN 98 
                     WHEN zc.duration BETWEEN 5.0 AND 100.0 THEN 101 
                   END 
                 WHEN zc.riesgo IN ( 'AA+', 'AA', 'AA-' ) THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND 1.0 THEN 93 
                     WHEN zc.duration BETWEEN 1.0 AND 3.0 THEN 96 
                     WHEN zc.duration BETWEEN 3.0 AND 5.0 THEN 99 
                     WHEN zc.duration BETWEEN 5.0 AND 30.0 THEN 102 
                   END 
                 WHEN zc.riesgo IN ( 'A+', 'A', 'A-' ) THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND 2.0 THEN 87 
                     WHEN zc.duration BETWEEN 2.0 AND 3.0 THEN 88 
                     WHEN zc.duration BETWEEN 3.0 AND 5.0 THEN 89 
                     WHEN zc.duration BETWEEN 5.0 AND 7.0 THEN 90 
                     WHEN zc.duration BETWEEN 7.0 AND 30.0 THEN 91 
                   END 
                 WHEN zc.riesgo IN ( 'BBB+', 'BBB', 'BBB-', 'BB+', 
                                     'BB', 'BB-', 'B+', 'B', 
                                     'B-', 'C' ) THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND 2.0 THEN 123 
                     WHEN zc.duration BETWEEN 2.0 AND 3.0 THEN 124 
                     WHEN zc.duration BETWEEN 3.0 AND 5.0 THEN 125 
                     WHEN zc.duration BETWEEN 5.0 AND 7.0 THEN 126 
                     WHEN zc.duration BETWEEN 7.0 AND 150.0 THEN 127 
                   END 
                 ELSE 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND 2.0 THEN 123 
                     WHEN zc.duration BETWEEN 2.0 AND 3.0 THEN 124 
                     WHEN zc.duration BETWEEN 3.0 AND 5.0 THEN 125 
                     WHEN zc.duration BETWEEN 5.0 AND 7.0 THEN 126 
                     WHEN zc.duration BETWEEN 7.0 AND 150.0 THEN 127 
                   END 
               END 
             WHEN zc.moneda = 'US$' AND f.Moneda <> 'US$' THEN 66 
             WHEN zc.moneda = 'US$' AND f.Moneda = 'US$' THEN 
                    CASE --mapping bonos latam
                        WHEN codigo_ins = 'AESGEN0529' THEN 264
                        WHEN codigo_ins = 'AESGEN0821' THEN 265
                        WHEN codigo_ins = 'AF241469' THEN 266
                        WHEN codigo_ins = 'AH007884' THEN 267
                        WHEN codigo_ins = 'ALFAA0324 ' THEN 268
                        WHEN codigo_ins = 'ALPEKA0823' THEN 269
                        WHEN codigo_ins = 'AUPIST0622' THEN 270
                        WHEN codigo_ins = 'BANGAN0425' THEN 271
                        WHEN codigo_ins = 'BBVASM0922' THEN 272
                        WHEN codigo_ins = 'BCENC0121 ' THEN 273
                        WHEN codigo_ins = 'BCOCPE0929' THEN 274
                        WHEN codigo_ins = 'BCOLO0621 ' THEN 275
                        WHEN codigo_ins = 'BCP1019   ' THEN 276
                        WHEN codigo_ins = 'BINTPE1020' THEN 277
                        WHEN codigo_ins = 'BRFGMB0926' THEN 278
                        WHEN codigo_ins = 'BRFSBZ0524' THEN 279
                        WHEN codigo_ins = 'CALLAO0423' THEN 280
                        WHEN codigo_ins = 'CDEL0925  ' THEN 281
                        WHEN codigo_ins = 'CENSUD0225' THEN 282
                        WHEN codigo_ins = 'CFELEC0227' THEN 283
                        WHEN codigo_ins = 'CMPCCI1918' THEN 284
                        WHEN codigo_ins = 'CMPCCI2204' THEN 285
                        WHEN codigo_ins = 'COFIDE0729' THEN 286
                        WHEN codigo_ins = 'CORJRL1121' THEN 287
                        WHEN codigo_ins = 'DAVIVI0118' THEN 288
                        WHEN codigo_ins = 'EC642125' THEN 289
                        WHEN codigo_ins = 'ECLCI0125 ' THEN 290
                        WHEN codigo_ins = 'ECOPET0626' THEN 291
                        WHEN codigo_ins = 'ECOPET0923' THEN 292
                        WHEN codigo_ins = 'ED286407' THEN 293
                        WHEN codigo_ins = 'ED825356' THEN 294
                        WHEN codigo_ins = 'EF068792' THEN 295
                        WHEN codigo_ins = 'PCU0735' THEN 296
                        WHEN codigo_ins = 'EF861855' THEN 297
                        WHEN codigo_ins = 'EG945302' THEN 298
                        WHEN codigo_ins = 'EG975321' THEN 299
                        WHEN codigo_ins = 'EG975325' THEN 300
                        WHEN codigo_ins = 'EH468926' THEN 301
                        WHEN codigo_ins = 'ECOPET0719' THEN 302
                        WHEN codigo_ins = 'EH967599' THEN 303
                        WHEN codigo_ins = 'EI015295' THEN 304
                        WHEN codigo_ins = 'EI032072' THEN 305
                        WHEN codigo_ins = 'EI036018' THEN 306
                        WHEN codigo_ins = 'EI054931' THEN 307
                        WHEN codigo_ins = 'EI112049' THEN 308
                        WHEN codigo_ins = 'TELVIS0140' THEN 309
                        WHEN codigo_ins = 'EI213380' THEN 310
                        WHEN codigo_ins = 'EI213384' THEN 311
                        WHEN codigo_ins = 'EI241890' THEN 312
                        WHEN codigo_ins = 'EI306294' THEN 313
                        WHEN codigo_ins = 'EI327873' THEN 314
                        WHEN codigo_ins = 'EI336211' THEN 315
                        WHEN codigo_ins = 'AMXLMM0340' THEN 316
                        WHEN codigo_ins = 'EI336243' THEN 317
                        WHEN codigo_ins = 'EI349086' THEN 318
                        WHEN codigo_ins = 'EI400317' THEN 319
                        WHEN codigo_ins = 'BCP0920' THEN 320
                        WHEN codigo_ins = 'EI419310' THEN 321
                        WHEN codigo_ins = 'EI467009' THEN 322
                        WHEN codigo_ins = 'EI507822' THEN 323
                        WHEN codigo_ins = 'EI600528' THEN 324
                        WHEN codigo_ins = 'EI627254' THEN 325
                        WHEN codigo_ins = 'EI637624' THEN 326
                        WHEN codigo_ins = 'EI675437' THEN 328
                        WHEN codigo_ins = 'EI757014' THEN 329
                        WHEN codigo_ins = 'EI810168' THEN 330
                        WHEN codigo_ins = 'EI868226' THEN 331
                        WHEN codigo_ins = 'EI939724' THEN 332
                        WHEN codigo_ins = 'EI992536' THEN 333
                        WHEN codigo_ins = 'EJ123001' THEN 334
                        WHEN codigo_ins = 'EJ141226' THEN 335
                        WHEN codigo_ins = 'EJ152916' THEN 336
                        WHEN codigo_ins = 'EJ237099' THEN 337
                        WHEN codigo_ins = 'EJ247759' THEN 338
                        WHEN codigo_ins = 'EJ276737' THEN 339
                        WHEN codigo_ins = 'EJ276742' THEN 340
                        WHEN codigo_ins = 'BCOCPE0822' THEN 341
                        WHEN codigo_ins = 'EJ341555' THEN 342
                        WHEN codigo_ins = 'EJ341560' THEN 343
                        WHEN codigo_ins = 'EJ350241' THEN 344
                        WHEN codigo_ins = 'BSANCI0922' THEN 345
                        WHEN codigo_ins = 'EJ363274' THEN 346
                        WHEN codigo_ins = 'EJ393172' THEN 347
                        WHEN codigo_ins = 'BSANTM1122' THEN 348
                        WHEN codigo_ins = 'EJ447299' THEN 349
                        WHEN codigo_ins = 'CENSUD0123' THEN 350
                        WHEN codigo_ins = 'GMEXIB1232' THEN 351
                        WHEN codigo_ins = 'EJ501005' THEN 352
                        WHEN codigo_ins = 'EJ548869' THEN 353
                        WHEN codigo_ins = 'EJ609917' THEN 354
                        WHEN codigo_ins = 'EJ611543' THEN 355
                        WHEN codigo_ins = 'EJ621340' THEN 356
                        WHEN codigo_ins = 'EJ627590' THEN 357
                        WHEN codigo_ins = 'TGPERU0428' THEN 358
                        WHEN codigo_ins = 'EJ654229' THEN 359
                        WHEN codigo_ins = 'EJ668899' THEN 360
                        WHEN codigo_ins = 'EJ668914' THEN 361
                        WHEN codigo_ins = 'EJ671705' THEN 362
                        WHEN codigo_ins = 'EJ682987' THEN 363
                        WHEN codigo_ins = 'EJ767592' THEN 364
                        WHEN codigo_ins = 'EJ828279' THEN 365
                        WHEN codigo_ins = 'ECOPET0943' THEN 366
                        WHEN codigo_ins = 'EJ836618' THEN 367
                        WHEN codigo_ins = 'EJ858949' THEN 368
                        WHEN codigo_ins = 'FRESLN1123' THEN 369
                        WHEN codigo_ins = 'EJ948876' THEN 370
                        WHEN codigo_ins = 'EJ948900' THEN 371
                        WHEN codigo_ins = 'EJ948972' THEN 372
                        WHEN codigo_ins = 'EK032439' THEN 373
                        WHEN codigo_ins = 'EK044884' THEN 374
                        WHEN codigo_ins = 'MINSUR0224' THEN 375
                        WHEN codigo_ins = 'EK141014' THEN 376
                        WHEN codigo_ins = 'EK164157' THEN 377
                        WHEN codigo_ins = 'EK165147' THEN 378
                        WHEN codigo_ins = 'EK172187' THEN 379
                        WHEN codigo_ins = 'EK174265' THEN 380
                        WHEN codigo_ins = 'EK244336' THEN 381
                        WHEN codigo_ins = 'EK254004' THEN 382
                        WHEN codigo_ins = 'EK265161' THEN 383
                        WHEN codigo_ins = 'ECOPET0545' THEN 384
                        WHEN codigo_ins = 'EK306386' THEN 385
                        WHEN codigo_ins = 'EK352999' THEN 386
                        WHEN codigo_ins = 'EK353005' THEN 387
                        WHEN codigo_ins = 'EK366169' THEN 388
                        WHEN codigo_ins = 'EK379309' THEN 389
                        WHEN codigo_ins = 'ENTEL0826' THEN 390
                        WHEN codigo_ins = 'EK483779' THEN 391
                        WHEN codigo_ins = 'EK485153' THEN 392
                        WHEN codigo_ins = 'EK487687' THEN 393
                        WHEN codigo_ins = 'EK499474' THEN 394
                        WHEN codigo_ins = 'EK518163' THEN 395
                        WHEN codigo_ins = 'EK563949' THEN 396
                        WHEN codigo_ins = 'EK568142' THEN 397
                        WHEN codigo_ins = 'GRUMAB1224' THEN 398
                        WHEN codigo_ins = 'EK741346' THEN 399
                        WHEN codigo_ins = 'EK870984' THEN 400
                        WHEN codigo_ins = 'EK892807' THEN 401
                        WHEN codigo_ins = 'EK901418' THEN 402
                        WHEN codigo_ins = 'EK951278' THEN 403
                        WHEN codigo_ins = 'EK964786' THEN 404
                        WHEN codigo_ins = 'LIMAMT0734' THEN 405
                        WHEN codigo_ins = 'ENAPCL0826' THEN 406
                        WHEN codigo_ins = 'ENAPCL1024' THEN 407
                        WHEN codigo_ins = 'ENRSIS1026' THEN 408
                        WHEN codigo_ins = 'ENTEL3024 ' THEN 409
                        WHEN codigo_ins = 'FERMAC0338' THEN 410
                        WHEN codigo_ins = 'FIBRBZ0127' THEN 411
                        WHEN codigo_ins = 'FUNOTR1224' THEN 412
                        WHEN codigo_ins = 'GGBRB0121 ' THEN 413
                        WHEN codigo_ins = 'GLBACO1019' THEN 414
                        WHEN codigo_ins = 'GLBACO1021' THEN 415
                        WHEN codigo_ins = 'GNLQCI0729' THEN 416
                        WHEN codigo_ins = 'GRUPOS0426' THEN 417
                        WHEN codigo_ins = 'KALLPA0526' THEN 418
                        WHEN codigo_ins = 'LIVEPL1026' THEN 419
                        WHEN codigo_ins = 'LW371842' THEN 420
                        WHEN codigo_ins = 'LW810722' THEN 421
                        WHEN codigo_ins = 'MEXCAT1026' THEN 422
                        WHEN codigo_ins = 'MXCHF0922 ' THEN 423
                        WHEN codigo_ins = 'OCENSA0521' THEN 424
                        WHEN codigo_ins = 'TERRAF1122' THEN 425
                        WHEN codigo_ins = 'QJ878935' THEN 426
                        WHEN codigo_ins = 'QJ879027' THEN 427
                        WHEN codigo_ins = 'VALEBZ0826' THEN 428
                        WHEN codigo_ins = 'RAIZBZ0127' THEN 429
                        WHEN codigo_ins = 'SCCO0425  ' THEN 430
                        WHEN codigo_ins = 'SIGMA0526 ' THEN 431
                        WHEN codigo_ins = 'SUAMSA0424' THEN 432
                        WHEN codigo_ins = 'TANNER0318' THEN 433
                        WHEN codigo_ins = 'TRAGSA0322' THEN 434
                        WHEN codigo_ins = 'TRANSM0523' THEN 435
                        WHEN codigo_ins = 'MIVIVI0123' THEN 436
                        WHEN codigo_ins = 'EMBRBZ0227' THEN 461
                        WHEN codigo_ins = 'EJ997555' THEN 446
                        WHEN codigo_ins = 'CMPCCI0427' THEN 474
                        WHEN codigo_ins = 'SUAMSA0427' THEN 475
                        WHEN codigo_ins = 'BINBUR0427' THEN 476
                        WHEN codigo_ins = 'CDEL0722' THEN 477
                        WHEN codigo_ins in ('TREA033122', 'TREA053122', 'TREA051527', 'TREA073122', 'TREA081527', 'TREA051018') THEN 478
                        WHEN codigo_ins = 'CELEO 0647' THEN 486
                        WHEN codigo_ins = 'CFELEC0124' THEN 488
                        WHEN codigo_ins = 'GLOPAR0327' THEN 489
                        WHEN codigo_ins = 'LATAIR1127' THEN 498
                        WHEN codigo_ins = 'SQM0125' THEN 500
                        WHEN codigo_ins = 'SQM0420' THEN 501
                        WHEN codigo_ins = 'MXCHF1119' THEN 502
                        WHEN codigo_ins = 'PETRPE0632' THEN 503
                        WHEN codigo_ins = 'CENSUD0727' THEN 504
                        WHEN codigo_ins = 'SUZANO0726' THEN 505
                        WHEN codigo_ins = 'BANBOG0827' THEN 507
                        WHEN codigo_ins = 'BANGEN0827' THEN 508
                        WHEN codigo_ins = 'KALLPA0827' THEN 509
                        WHEN codigo_ins = 'PEMEX0327' THEN 511
                        WHEN codigo_ins = 'SUZANO1426' THEN 512
                        WHEN codigo_ins = 'BISTPP0922' THEN 513
                        WHEN codigo_ins = 'AEIUS0927' THEN 514
                        WHEN codigo_ins = 'MEXCAT0428' THEN 515
                        WHEN codigo_ins = 'MEXCAT0747' THEN 516
                        WHEN codigo_ins = 'MXCHF1027' THEN 517
                        WHEN codigo_ins = 'MXCHF0148' THEN 518
                        WHEN codigo_ins = 'BRASKM0123' THEN 519
                        WHEN codigo_ins = 'BRASKM0128' THEN 520
                        WHEN codigo_ins = 'COLBUN1027' THEN 521
                        WHEN codigo_ins = 'GGBRBZ1027' THEN 522
                        WHEN codigo_ins = 'INTFSI1027' THEN 523
                        WHEN codigo_ins = 'BFALA1027' THEN 525
                        WHEN codigo_ins = 'CELARA1127' THEN 526
                        WHEN codigo_ins = 'MULT1122' THEN 529
                        WHEN codigo_ins = 'FIBRBZ0125' THEN 531
                    END
           END 
         WHEN zc.tipo_instrumento = 'Deposito' 
               OR tipo_instrumento = 'Factura' THEN -- Mapping liquidez    
           CASE 
             WHEN zc.moneda = '$' THEN 
               CASE 
                 WHEN zc.duration BETWEEN 0.0 AND ( 7.0 / 365.0 ) THEN 144 
                 WHEN zc.duration BETWEEN ( 7.0 / 365.0 ) AND ( 30.0 / 365.0 ) 
               THEN 147 
                 WHEN zc.duration BETWEEN ( 30.0 / 365.0 ) AND ( 60.0 / 365.0 ) 
               THEN 
                 149 
                 WHEN zc.duration BETWEEN ( 60.0 / 365.0 ) AND ( 90.0 / 365.0 ) 
               THEN 
                 151 
                 WHEN zc.duration BETWEEN ( 90.0 / 365.0 ) AND ( 120.0 / 365.0 ) 
               THEN 
                 146 
                 WHEN zc.duration BETWEEN ( 120.0 / 365.0 ) AND 
                                          ( 150.0 / 365.0 ) THEN 
                 148 
                 WHEN zc.duration BETWEEN ( 150.0 / 365.0 ) AND 
                                          ( 180.0 / 365.0 ) THEN 
                 150 
                 WHEN zc.duration BETWEEN ( 180.0 / 365.0 ) AND 
                                          ( 270.0 / 365.0 ) THEN 
                 152 
                 WHEN zc.duration BETWEEN ( 270.0 / 365.0 ) AND ( 1.0 ) THEN 145 
                 WHEN zc.duration BETWEEN ( 1.0 ) AND ( 30.0 ) THEN 153 
               END 
             WHEN zc.moneda = 'UF' THEN 
               CASE 
                 WHEN zc.duration BETWEEN 0.0 AND ( 7.0 / 365.0 ) THEN 155 
                 WHEN zc.duration BETWEEN ( 7.0 / 365.0 ) AND ( 30.0 / 365.0 ) 
               THEN 161 
                 WHEN zc.duration BETWEEN ( 30.0 / 365.0 ) AND ( 60.0 / 365.0 ) 
               THEN 
                 162 
                 WHEN zc.duration BETWEEN ( 60.0 / 365.0 ) AND ( 90.0 / 365.0 ) 
               THEN 
                 163 
                 WHEN zc.duration BETWEEN ( 90.0 / 365.0 ) AND ( 120.0 / 365.0 ) 
               THEN 
                 156 
                 WHEN zc.duration BETWEEN ( 120.0 / 365.0 ) AND 
                                          ( 150.0 / 365.0 ) THEN 
                 157 
                 WHEN zc.duration BETWEEN ( 150.0 / 365.0 ) AND 
                                          ( 180.0 / 365.0 ) THEN 
                 158 
                 WHEN zc.duration BETWEEN ( 180.0 / 365.0 ) AND 
                                          ( 270.0 / 365.0 ) THEN 
                 160 
                 WHEN zc.duration BETWEEN ( 270.0 / 365.0 ) AND ( 1.0 ) THEN 159 
                 WHEN zc.duration BETWEEN ( 1.0 ) AND ( 30.0 ) THEN 154 
               END 
             WHEN zc.moneda = 'US$' THEN 
               CASE 
                 WHEN f.moneda = '$' THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND ( 15.0 / 365.0 ) THEN 170 
                     WHEN zc.duration BETWEEN ( 15.0 / 365.0 ) AND ( 30.0 / 
                                              365.0 ) 
                   THEN 
                     173 
                     WHEN zc.duration BETWEEN ( 30.0 / 365.0 ) AND ( 60.0 / 
                                              365.0 ) 
                   THEN 
                     175 
                     WHEN zc.duration BETWEEN ( 60.0 / 365.0 ) AND ( 90.0 / 
                                              365.0 ) 
                   THEN 
                     176 
                     WHEN zc.duration BETWEEN ( 90.0 / 365.0 ) AND 
                                              ( 180.0 / 365.0 ) 
                   THEN 
                     171 
                     WHEN zc.duration BETWEEN ( 180.0 / 365.0 ) AND 
                                              ( 270.0 / 365.0 ) 
                   THEN 
                     172 
                     WHEN zc.duration BETWEEN ( 270.0 / 365.0 ) AND 
                                              ( 360.0 / 365.0 ) 
                   THEN 
                     174 
                   END 
                 WHEN f.moneda = 'US$' THEN 
                   CASE 
                     WHEN zc.duration BETWEEN 0.0 AND ( 7.0 / 365.0 ) THEN 144 
                     WHEN zc.duration BETWEEN ( 7.0 / 365.0 ) AND 
                                              ( 30.0 / 365.0 ) THEN 
                     147 
                     WHEN zc.duration BETWEEN ( 30.0 / 365.0 ) AND ( 60.0 / 
                                              365.0 ) 
                   THEN 
                     149 
                     WHEN zc.duration BETWEEN ( 60.0 / 365.0 ) AND ( 90.0 / 
                                              365.0 ) 
                   THEN 
                     151 
                     WHEN zc.duration BETWEEN ( 90.0 / 365.0 ) AND 
                                              ( 120.0 / 365.0 ) 
                   THEN 
                     146 
                     WHEN zc.duration BETWEEN ( 120.0 / 365.0 ) AND 
                                              ( 150.0 / 365.0 ) 
                   THEN 
                     148 
                     WHEN zc.duration BETWEEN ( 150.0 / 365.0 ) AND 
                                              ( 180.0 / 365.0 ) 
                   THEN 
                     150 
                     WHEN zc.duration BETWEEN ( 180.0 / 365.0 ) AND 
                                              ( 270.0 / 365.0 ) 
                   THEN 
                     152 
                     WHEN zc.duration BETWEEN ( 270.0 / 365.0 ) AND ( 1.0 ) THEN 
                     145 
                     WHEN zc.duration BETWEEN ( 1.0 ) AND ( 30.0 ) THEN 153 
                   END 
               END 
           END 
         WHEN zc.tipo_instrumento = 'Letra Hipotecaria' THEN 
           -- Mapping letras    
           CASE 
             WHEN zc.moneda = 'UF' THEN 
               CASE 
                 WHEN zc.duration BETWEEN 0.0 AND ( 7.0 / 365.0 ) THEN 155 
                 WHEN zc.duration BETWEEN ( 7.0 / 365.0 ) AND ( 30.0 / 365.0 ) 
               THEN 161 
                 WHEN zc.duration BETWEEN ( 30.0 / 365.0 ) AND ( 60.0 / 365.0 ) 
               THEN 
                 162 
                 WHEN zc.duration BETWEEN ( 60.0 / 365.0 ) AND ( 90.0 / 365.0 ) 
               THEN 
                 163 
                 WHEN zc.duration BETWEEN ( 90.0 / 365.0 ) AND ( 120.0 / 365.0 ) 
               THEN 
                 156 
                 WHEN zc.duration BETWEEN ( 120.0 / 365.0 ) AND 
                                          ( 150.0 / 365.0 ) THEN 
                 157 
                 WHEN zc.duration BETWEEN ( 150.0 / 365.0 ) AND 
                                          ( 180.0 / 365.0 ) THEN 
                 158 
                 WHEN zc.duration BETWEEN ( 180.0 / 365.0 ) AND 
                                          ( 270.0 / 365.0 ) THEN 
                 160 
                 WHEN zc.duration BETWEEN ( 270.0 / 365.0 ) AND ( 1.0 ) THEN 159 
                 WHEN zc.duration BETWEEN ( 1.0 ) AND ( 30.0 ) THEN 154 
               END 
           END 
         WHEN zc.tipo_instrumento = 'Accion' THEN -- Mapping acciones Chile   
           CASE 
             WHEN codigo_ins = 'AESGENER' THEN 184 
             WHEN codigo_ins = 'AGUAS-A' THEN 185 
             WHEN codigo_ins = 'ANDINA-B' THEN 186 
             WHEN codigo_ins = 'ANTARCHILE' THEN 187 
             WHEN codigo_ins = 'AQUACHILE' THEN 188 
             WHEN codigo_ins = 'BANMEDICA' THEN 189 
             WHEN codigo_ins = 'BANVIDA' THEN 190 
             WHEN codigo_ins = 'BCI' THEN 191 
             WHEN codigo_ins = 'BESALCO' THEN 192 
             WHEN codigo_ins = 'BLUMAR' THEN 193 
             WHEN codigo_ins = 'BSANTANDER' THEN 194 
             WHEN codigo_ins = 'CAMANCHACA' THEN 195 
             WHEN codigo_ins = 'CAP' THEN 196 
             WHEN codigo_ins = 'CCU' THEN 197 
             WHEN codigo_ins = 'CEMENTOS' THEN 198 
             WHEN codigo_ins = 'CENCOSUD' THEN 199 
             WHEN codigo_ins = 'CHILE' THEN 200 
             WHEN codigo_ins = 'CMPC' THEN 201 
             WHEN codigo_ins = 'COLBUN' THEN 202 
             WHEN codigo_ins = 'CONCHATORO' THEN 203 
             WHEN codigo_ins = 'COPEC' THEN 204 
             WHEN codigo_ins = 'CRISTALES' THEN 205 
             WHEN codigo_ins = 'CTC-A' THEN 206 
             WHEN codigo_ins = 'ECL' THEN 207 
             WHEN codigo_ins = 'EMBONOR-B' THEN 208 
             WHEN codigo_ins = 'ENJOY' THEN 209 
             WHEN codigo_ins = 'ENTEL' THEN 210 
             WHEN codigo_ins = 'FALABELLA' THEN 211 
             WHEN codigo_ins = 'FORUS' THEN 212 
             WHEN codigo_ins = 'FOSFOROS' THEN 213 
             WHEN codigo_ins = 'GASCO' THEN 214 
             WHEN codigo_ins = 'GNCHILE' THEN 215 
             WHEN codigo_ins = 'HABITAT' THEN 216 
             WHEN codigo_ins = 'HF' THEN 217 
             WHEN codigo_ins = 'HITES' THEN 218 
             WHEN codigo_ins = 'IAM' THEN 219 
             WHEN codigo_ins = 'IANSA' THEN 220 
             WHEN codigo_ins = 'ILC' THEN 221 
             WHEN codigo_ins = 'INDISA' THEN 222 
             WHEN codigo_ins = 'INTEROCEAN' THEN 223 
             WHEN codigo_ins = 'ITAUCORP' THEN 224 
             WHEN codigo_ins = 'NUEVAPOLAR' THEN 225 
             WHEN codigo_ins = 'LAN' THEN 226
             WHEN codigo_ins = 'LTM' THEN 226 
             WHEN codigo_ins = 'LAS CONDES' THEN 227 
             WHEN codigo_ins = 'MASISA' THEN 228 
             WHEN codigo_ins = 'MINERA' THEN 229 
             WHEN codigo_ins = 'MOLYMET' THEN 230 
             WHEN codigo_ins = 'MULTIFOODS' THEN 232 
             WHEN codigo_ins = 'NAVIERA' THEN 233 
             WHEN codigo_ins = 'NUEVAPOLAR' THEN 234 
             WHEN codigo_ins = 'PARAUCO' THEN 235 
             WHEN codigo_ins = 'PAZ' THEN 236 
             WHEN codigo_ins = 'PEHUENCHE' THEN 237 
             WHEN codigo_ins = 'PILMAIQUEN' THEN 238 
             WHEN codigo_ins = 'PROVIDA' THEN 239 
             WHEN codigo_ins = 'PUCOBRE-A' THEN 240 
             WHEN codigo_ins = 'RIPLEY' THEN 241 
             WHEN codigo_ins = 'SALFACORP' THEN 242 
             WHEN codigo_ins = 'SECURITY' THEN 243 
             WHEN codigo_ins = 'SK' THEN 244 
             WHEN codigo_ins = 'SMSAAM' THEN 245 
             WHEN codigo_ins = 'SOCOVESA' THEN 246 
             WHEN codigo_ins = 'SONDA' THEN 247 
             WHEN codigo_ins = 'SQM-B' THEN 248 
             WHEN codigo_ins = 'VAPORES' THEN 250 
             WHEN codigo_ins = 'VOLCAN' THEN 251 
             WHEN codigo_ins = 'VSPT' THEN 252 
             WHEN codigo_ins = 'WATTS' THEN 253 
             WHEN codigo_ins = 'ZOFRI' THEN 254 
             WHEN codigo_ins = 'ENELCHILE' THEN 255 
             WHEN codigo_ins = 'ENELGXCH' THEN 256 
             WHEN codigo_ins = 'SM-CHILE B' THEN 258 
             WHEN codigo_ins = 'QUINENCO' THEN 259 
             WHEN codigo_ins = 'ENDESA-AM' THEN 260 
             WHEN codigo_ins = 'LIPIGAS' THEN 261
             WHEN codigo_ins = 'ENELAM' THEN 257
             WHEN codigo_ins = 'SMU' THEN 438
             WHEN codigo_ins = 'ORO BLANCO' THEN 460
             WHEN codigo_ins = 'TRICOT' THEN 510
             WHEN codigo_ins = 'EISA' THEN 524
           END
         ELSE 0 
       END                                                  AS Index_Id, 
       zc.sector                                            AS sector, 
       zc.riesgo_internacional                              AS riesgo_internacional,
       zc.tipo_ra                                           AS tipo_ra
FROM   dbo.zhis_carteras_recursive zc, 
       fondosir f 
WHERE  zc.codigo_fdo = f.codigo_fdo COLLATE database_default 
       AND f.info_invest = 1 
       AND (zc.tipo_instrumento <> 'FX' or zc.tipo_instrumento is null)
       -- La caja la sacamos del balance contable   
       AND fecha = 'AUTODATE'
     AND zc.codigo_fdo = 'AUTOFUND' 
UNION ALL -- Se computa la posicion forward long leg   
SELECT 'AUTODATE'                         AS fecha, 
       Ltrim(Rtrim(fwm.codigo_fdo))         AS codigo_fdo, 
       Ltrim(Rtrim(fwm.codigo_emi))         AS codigo_emi, 
       Ltrim(Rtrim(fwm.codigo_ins))         AS codigo_ins, 
       'FX Forward'                         AS tipo_instrumento, 
       CASE --PASAMOS MONEDAS AL FORMATO CORRECTO    
         WHEN fwm.moneda_compra = 'USD' THEN 'US$' 
         WHEN fwm.moneda_compra = 'CLP' THEN '$' 
         WHEN fwm.moneda_compra = 'UF' THEN 'UF' 
         WHEN fwm.moneda_compra = 'EUR' THEN 'EU' 
       END                                  AS moneda, 
       CASE 
         -- valorizamos los forward a precio spot para la posicion larga en pesos   
         WHEN f.moneda = '$' THEN -- valorizamos forwards en fondo en pesos 
           CASE 
             WHEN fwm.moneda_compra = 'CLP' THEN nominal_compra 
             WHEN fwm.moneda_compra = 'USD' THEN 
             nominal_compra * (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 66 
             AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_compra = 'MXN' THEN 
             nominal_compra * (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 85 
             AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_compra = 'EUR' THEN 
             nominal_compra * (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 73 
             AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_compra = 'UF' THEN 
             nominal_compra * (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 72 
             AND fecha = 'AUTODATE') 
           END 
         WHEN f.moneda = 'US$' THEN -- valorizamos forwards en fondo en dolares 
           CASE 
             WHEN fwm.moneda_compra = 'USD' THEN nominal_compra 
             WHEN fwm.moneda_compra = '$' THEN 
             nominal_compra / (SELECT valor 
                               FROM   indices_dinamica 
                               WHERE 
             index_id = 66 
             AND fecha = 'AUTODATE') 
           END 
       END                                  AS Monto, 
       0                                    AS nominal, 
       0                                    AS cantidad, 
       0                                    AS precio, 
       0                                    AS duration, 
       0                                    AS tasa, 
       'N/A'                                AS riesgo, 
       Ltrim(Rtrim(emisores.nombre_emisor)) AS nombre_emisor, 
       'Forward ' + ' ' + emisores.nombre_emisor 
       + ' long leg'                        AS nombre_instrumento, 
       fwm.fecha_vcto                       AS fec_vtco,  
       'N/A'                                 AS pais_emisor, 
       CASE --Mapeamos los forwards de moneda a los distintos indices   
         WHEN fwm.estrategia = 'Hedge CLP Lebac' THEN 0
         WHEN fwm.moneda_compra = 'CLP' THEN 0 
         WHEN fwm.moneda_compra = 'USD' THEN 66 
         WHEN fwm.moneda_compra = 'MXN' THEN 85 
         WHEN fwm.moneda_compra = 'EUR' THEN 73
         WHEN fwm.moneda_compra = 'UF' THEN 72 
       END                                  AS index_id, 
       'Forwards'                           AS sector,
       'N/A'                                AS riesgo_internacional,
       'Forward'                            AS tipo_ra 
FROM   fwd_monedas_estatica FWM 
       LEFT OUTER JOIN emisores 
                    ON fwm.codigo_emi = emisores.codigo_emi, 
       fondosir F 
WHERE  FWM.codigo_fdo = F.codigo_fdo 
       AND FWM.fecha_op <= 'AUTODATE' 
       AND FWM.fecha_vcto > 'AUTODATE'
     AND FWM.codigo_fdo = 'AUTOFUND'  
UNION ALL -- Se computa la posicion forward short leg   
SELECT 'AUTODATE'                         AS fecha, 
       Ltrim(Rtrim(fwm.codigo_fdo))         AS codigo_fdo, 
       Ltrim(Rtrim(fwm.codigo_emi))         AS codigo_emi, 
       Ltrim(Rtrim(fwm.codigo_ins))         AS codigo_ins, 
       'FX Forward'                         AS tipo_instrumento, 
       CASE --PASAMOS MONEDAS AL FORMATO CORRECTO    
         WHEN fwm.moneda_venta = 'USD' THEN 'US$' 
         WHEN fwm.moneda_venta = 'CLP' THEN '$' 
         WHEN fwm.moneda_venta = 'UF' THEN 'UF' 
         WHEN fwm.moneda_venta = 'EUR' THEN 'EU' 
       END                                  AS moneda, 
       CASE 
         -- valorizamos los forward a precio spot para la posicion corta, es negativo ya que es una posicion pasiva
         WHEN f.moneda = '$' THEN -- valorizamos para fondo en pesos 
           CASE 
             WHEN fwm.moneda_venta = 'CLP' THEN -1 * nominal_venta 
             WHEN fwm.moneda_venta = 'USD' THEN 
             -1 * nominal_venta * (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 66 
                                          AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_venta = 'MXN' THEN 
             -1 * nominal_venta * (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 85 
                                          AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_venta = 'EUR' THEN 
             -1 * nominal_venta * (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 73 
                                          AND fecha = 'AUTODATE') 
             WHEN fwm.moneda_venta = 'UF' THEN 
             -1 * nominal_venta * (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 72 
                                          AND fecha = 'AUTODATE') 
           END 
         WHEN f.moneda = 'US$' THEN --Valorizamos para fondo en dolares 
           CASE 
             WHEN fwm.moneda_venta = 'USD' THEN -1 * nominal_venta 
             WHEN fwm.moneda_venta = 'CLP' THEN 
             -1 * nominal_venta / (SELECT valor 
                                   FROM   indices_dinamica 
                                   WHERE  index_id = 66 
                                          AND fecha = 'AUTODATE') 
           END 
       END                                  AS Monto, 
       0                                    AS nominal, 
       0                                    AS cantidad, 
       0                                    AS precio, 
       0                                    AS duration, 
       0                                    AS tasa, 
       'N/A'                                AS riesgo, 
       Ltrim(Rtrim(emisores.nombre_emisor)) AS nombre_emisor, 
       'Forward ' + ' ' + emisores.nombre_emisor 
       + ' short leg'                       AS nombre_instrumento, 
       fwm.fecha_vcto                       AS fec_vtco, 
       'N/A'                                 AS pais_emisor, 
       CASE --Mapeamos los forwards de moneda a los distintos indices
         WHEN fwm.estrategia = 'Hedge CLP Lebac' THEN 0 
         WHEN fwm.moneda_venta = 'CLP' THEN 0 
         WHEN fwm.moneda_venta = 'USD' THEN 66 
         WHEN fwm.moneda_venta = 'MXN' THEN 85 
         WHEN fwm.moneda_venta = 'EUR' THEN 73 
         WHEN fwm.moneda_venta = 'UF' THEN 72 
       END                                  AS index_id, 
       'Forwards'                           AS sector,
       'N/A'                                AS riesgo_internacional,
       'Forward'                            AS tipo_ra
FROM   fwd_monedas_estatica FWM 
       LEFT OUTER JOIN emisores 
                    ON fwm.codigo_emi = emisores.codigo_emi, 
       fondosir F 
WHERE  FWM.codigo_fdo = F.codigo_fdo 
       AND F.info_invest = 1 
       AND FWM.fecha_op <= 'AUTODATE' 
       AND FWM.fecha_vcto > 'AUTODATE'
     AND FWM.codigo_fdo = 'AUTOFUND' 
UNION ALL 
-- Se computa la posicion de las cajas de fondos mutuos, notar que se desagraga entre cuenta de activos y pasivos
SELECT 'AUTODATE'                                AS fecha, 
       Ltrim(Rtrim(Balance.codigo_fdo))            AS codigo_fdo, 
       'CAJA ' + Ltrim(Rtrim(Balance.codigo_fdo))  AS codigo_emi, 
       'CAJA '  + Balance.moneda + ' '  + Ltrim(Rtrim(LEFT(Balance.codigo_cta, 1))) AS codigo_ins, 
       'FX'                                        AS tipo_instrumento, 
       Balance.moneda                              AS moneda, 
       CASE 
         WHEN LEFT(Balance.codigo_cta, 1) = 1 THEN Sum(Balance.balance) 
         ELSE -1 * Sum(Balance.balance) 
       END                                         AS monto, 
       0.0                                         AS nominal, 
       0                                           AS cantidad, 
       0                                           AS precio, 
       0                                           AS duration, 
       0                                           AS tasa, 
       'N/A'                                       AS riesgo, 
       'Caja'                                      AS nombre_emisor, 
       CASE 
         WHEN LEFT(Balance.codigo_cta, 1) = 1 THEN 
         'Caja Activos ' + Balance.moneda 
         ELSE 'Caja Pasivos ' + Balance.moneda 
       END                                         AS nombre_instrumento, 
       'AUTODATE'                                AS fec_vcto, 
       'N/A'                                        AS pais_emisor, 
       CASE --Mapeamos las cajas a los distintos indices    
         WHEN MAX(f.Moneda) = '$' THEN
     CASE
     WHEN Balance.moneda = '$' THEN 0 
         WHEN Balance.moneda = 'US$' THEN 66 
         WHEN Balance.moneda = 'MXN' THEN 85 
         WHEN Balance.moneda = 'EU' THEN 73
     END 
         WHEN MAX(f.Moneda) = 'US$' THEN
     CASE
     WHEN Balance.moneda = '$' THEN 66 
         WHEN Balance.moneda = 'US$' THEN 0 
         WHEN Balance.moneda = 'MXN' THEN 85 
         WHEN Balance.moneda = 'EU' THEN 73
     END 
       END                                         AS index_id, 
       'Caja'                                      AS sector,
       'N/A'                                AS riesgo_internacional,
       'Caja'                               AS tipo_ra
FROM   (SELECT pc.codigo_fdo, 
               pc.periodo, 
               pc.codigo_cta, 
               pc.nombre_cta, 
               CASE 
                 WHEN pc.codigo_cta IN ( '101001001003', '101001001004', 
                                         '101001002001' 
                                         , 
                                         '101001002003', 
                                         '101001002002', '101001002004', 
                                         '101001002006', '201001001008'
                                       ) THEN 
                 'US$' 
                 WHEN pc.codigo_cta IN ( '101001001001', '101001001002', 
                                         '101001001004' 
                                         , 
                                         '101001001005', 
                                         '101001001008', '101003001001', 
                                         '101003001003' 
                                         , 
                                                '201001001002', '201001001003' ) 
               THEN 
                 '$' 
                 WHEN pc.codigo_cta IN ( '101001002013', '201001001001', '201001001009' ) THEN 
                 'EU' 
               END AS moneda, 
               CASE 
                 WHEN LEFT(pc.codigo_cta, 1) = 1 THEN 
                 pc.[debe_01] + pc.[debe_02] + pc.[debe_03] 
               + pc.[debe_04] + pc.[debe_05] + pc.[debe_06] 
               + pc.[debe_07] + pc.[debe_08] + pc.[debe_09] 
               + pc.[debe_10] + pc.[debe_11] + pc.[debe_12] - pc.[haber_01] - 
                 pc.[haber_02] 
                                                      - pc.[haber_03] - 
                 pc.[haber_04] - 
                 pc.[haber_05] - pc.[haber_06] - pc.[haber_07] - pc.[haber_08] - 
                 pc.[haber_09] 
               - pc.[haber_10] - pc.[haber_11] - pc.[haber_12] 
                 ELSE pc.[haber_01] + pc.[haber_02] + pc.[haber_03] 
                      + pc.[haber_04] + pc.[haber_05] + pc.[haber_06] 
                      + pc.[haber_07] + pc.[haber_08] + pc.[haber_09] 
                      + pc.[haber_10] + pc.[haber_11] + pc.[haber_12] - 
                      pc.[debe_01] - 
                      pc.[debe_02] 
                             - pc.[debe_03] - pc.[debe_04] - pc.[debe_05] - 
                      pc.[debe_06] - 
                             pc.[debe_07] - pc.[debe_08] - pc.[debe_09] - 
                      pc.[debe_10] 
                      - 
                      pc.[debe_11] - pc.[debe_12] 
               END AS balance 
        FROM   [BCS11384].[BDPFM1].dbo.fm_plan_cuentas pc, 
               fondosir f 
        WHERE  periodo = LEFT('AUTODATE', 4) 
               AND f.codigo_fdo = pc.codigo_fdo COLLATE database_default AND f.codigo_fdo IN ('MACRO CLP3', 'MACRO 1.5', 'IMT E-PLUS', 'RENTA')
               AND f.codigo_fdo = 'AUTOFUND' 
               AND F.info_invest = 1 
               AND pc.codigo_cta IN ( '101001001003', '101001001004', 
                                      '101001002001', 
                                      '101001002003', 
                                      '101001002002', '101001002004', 
                                      '101001002006', 
                                          '101001001001', 
                                      '101001001002', '101001001004', 
                                      '101001001005', 
                                          '101001001008', 
                                      '101003001001', '101003001003', 
                                      '201001001002', 
                                          '201001001003', 
                                      '101001002013', '201001001001', '201001001008', '201001001009' )) Balance
                    left outer join fondosir f on f.Codigo_Fdo = Balance.codigo_fdo collate database_default
GROUP  BY Balance.codigo_fdo, 
          LEFT(Balance.codigo_cta, 1), 
          Balance.moneda 
UNION ALL 
-- Se computa la posicion de las cajas de fondos de inversion, notar que se desagraga entre cuenta de activos y pasivos
SELECT 'AUTODATE'                                AS fecha, 
       Ltrim(Rtrim(Balance.codigo_fdo))            AS codigo_fdo, 
       'CAJA ' + Ltrim(Rtrim(Balance.codigo_fdo))  AS codigo_emi, 
       'CAJA '  + Balance.moneda + ' '  + Ltrim(Rtrim(LEFT(Balance.codigo_cta, 1))) AS codigo_ins, 
       CASE 
       WHEN Balance.moneda = 'Leverage' THEN 'Leverage' 
       ELSE 'FX'
                                               END AS tipo_instrumento, 
       Balance.moneda                              AS moneda, 
       CASE 
         WHEN LEFT(Balance.codigo_cta, 1) = 1 THEN Sum(Balance.balance) 
         ELSE -1 * Sum(Balance.balance) 
       END                                         AS monto, 
       0.0                                         AS nominal, 
       0                                           AS cantidad, 
       0                                           AS precio, 
       0                                           AS duration, 
       0                                           AS tasa, 
       'N/A'                                       AS riesgo, 
       'Caja'                                      AS nombre_emisor, 
       CASE 
         WHEN LEFT(Balance.codigo_cta, 1) = 1 THEN 
         'Caja Activos ' + Balance.moneda 
         ELSE 'Caja Pasivos ' + Balance.moneda 
       END                                         AS nombre_instrumento, 
       'AUTODATE'                                AS fec_vcto, 
       'N/A'                                        AS pais_emisor, 
       CASE --Mapeamos las cajas a los distintos indices    
         WHEN MAX(f.Moneda) = '$' THEN
     CASE
     WHEN Balance.moneda = '$' THEN 0 
     WHEN Balance.moneda = 'Leverage' THEN 0
     WHEN Balance.moneda = 'US$' THEN 66 
     WHEN Balance.moneda = 'MXN' THEN 85 
     WHEN Balance.moneda = 'EU' THEN 73
     END 
         WHEN MAX(f.Moneda) = 'US$' THEN
     CASE
     WHEN Balance.moneda = '$' THEN 66 
     WHEN Balance.moneda = 'US$' THEN 0 
     WHEN Balance.moneda = 'MXN' THEN 85 
     WHEN Balance.moneda = 'EU' THEN 73
     END 
       END                                         AS index_id, 
       'Caja'                                      AS sector,
       'N/A'                                AS riesgo_internacional,
       'Caja'                               AS tipo_ra
FROM   (SELECT pc.codigo_fdo, 
               pc.periodo, 
               pc.codigo_cta, 
               pc.nombre_cta, 
               CASE 
                 WHEN pc.codigo_cta IN ( '101001001003', '101001002001', 
                                         '101001002002' 
                                         , 
                                         '101001002004' ) THEN 'US$' 
                 WHEN pc.codigo_cta IN ( '101001001001', '101001001002', 
                                         '101001001004' 
                                         , 
                                         '101001001005', 
                                         '101001001008', '101003001001', 
                                         '101003001003' 
                                         , 
                                                '201001001002', 
                                         '201001001003', '201001001006', '201001001004') THEN 
                 '$' 
                 WHEN pc.codigo_cta IN ( '101001002003', '201001001001' ) THEN 
                 'EU' 
                 WHEN pc.codigo_cta IN ( '201010060', '201010100' ) THEN 
                 'Leverage' 
               END AS moneda, 
               CASE 
                 WHEN LEFT(pc.codigo_cta, 1) = 1 THEN 
                 pc.[debe_01] + pc.[debe_02] + pc.[debe_03] 
               + pc.[debe_04] + pc.[debe_05] + pc.[debe_06] 
               + pc.[debe_07] + pc.[debe_08] + pc.[debe_09] 
               + pc.[debe_10] + pc.[debe_11] + pc.[debe_12] - pc.[haber_01] - 
                 pc.[haber_02] 
                                                      - pc.[haber_03] - 
                 pc.[haber_04] - 
                 pc.[haber_05] - pc.[haber_06] - pc.[haber_07] - pc.[haber_08] - 
                 pc.[haber_09] 
               - pc.[haber_10] - pc.[haber_11] - pc.[haber_12] 
                 ELSE pc.[haber_01] + pc.[haber_02] + pc.[haber_03] 
                      + pc.[haber_04] + pc.[haber_05] + pc.[haber_06] 
                      + pc.[haber_07] + pc.[haber_08] + pc.[haber_09] 
                      + pc.[haber_10] + pc.[haber_11] + pc.[haber_12] - 
                      pc.[debe_01] - 
                      pc.[debe_02] 
                             - pc.[debe_03] - pc.[debe_04] - pc.[debe_05] - 
                      pc.[debe_06] - 
                             pc.[debe_07] - pc.[debe_08] - pc.[debe_09] - 
                      pc.[debe_10] 
                      - 
                      pc.[debe_11] - pc.[debe_12] 
               END AS balance 
        FROM   [BCS11384].[BDPFM2].dbo.fm_plan_cuentas pc, 
               fondosir f 
        WHERE  periodo = LEFT('AUTODATE', 4) 
               AND f.codigo_fdo = pc.codigo_fdo COLLATE database_default 
               AND f.codigo_fdo = 'AUTOFUND' AND f.codigo_fdo IN ('MACRO CLP3', 'MACRO 1.5', 'IMT E-PLUS', 'RENTA')
               AND F.info_invest = 1 
               AND pc.codigo_cta IN ( '101001001003', '101001002001', 
                                      '101001002002', 
                                      '101001002004', 
                                      '101001002003', '201001001001', 
                                      '101001001001', 
                                          '101001001002', 
                                      '101001001004', '101001001005', 
                                      '101001001008', 
                                          '101003001001', 
                                      '101003001003', '201001001002', 
                                      '201001001003', 
                                          '201001001006', '201010100', '201001001004','201010060')) Balance 
                    left outer join fondosir f on f.Codigo_Fdo = Balance.codigo_fdo collate database_default
GROUP  BY Balance.codigo_fdo, 
          LEFT(Balance.codigo_cta, 1), 
          Balance.moneda 