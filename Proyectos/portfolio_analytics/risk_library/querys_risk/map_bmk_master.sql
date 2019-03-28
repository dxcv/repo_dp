/*     
Created on Tue Jan 17 11:00:00 2017      
@author: Fernando Suarez      
Consulta para mapear la cartera de los distintos benchmarks a sus respectivs indices representativos. 
*/ 
-- La consulta primero computa el mapeo de los instrumentos de la cartera ex derivados ex caja
SELECT zc.fecha, 
       zc.benchmark_id, 
       ltrim(rtrim(zc.codigo_ins)) as codigo_ins,
       CASE 
          WHEN f.estrategia = 'credito' then 'Bono Corporativo' 
          WHEN f.estrategia = 'renta variable' then 'Accion'
     END AS tipo_instrumento,
       zc.weight AS weight, 
       zc.moneda, 
       zc.tasa, 
       zc.duration, 
       zc.riesgo,
       -- Aca empieza el mapeo de los instrumentos a indices representativos 
       -- Empezamos con bonos
       CASE 
         WHEN zc.moneda = '$' THEN  -- Mapping para bonos en pesos
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
           END --MAPPING ACCIONES CHILE
                WHEN zc.Codigo_Ins = 'AESGENER' THEN  184
                WHEN zc.Codigo_Ins = 'AGUAS-A' THEN   185
                WHEN zc.Codigo_Ins = 'ANDINA-B' THEN  186
                WHEN zc.Codigo_Ins = 'ANTARCHILE' THEN  187
                WHEN zc.Codigo_Ins = 'AQUACHILE' THEN   188
                WHEN zc.Codigo_Ins = 'BANMEDICA' THEN   189
                WHEN zc.Codigo_Ins = 'BANVIDA' THEN   190
                WHEN zc.Codigo_Ins = 'BCI' THEN   191
                WHEN zc.Codigo_Ins = 'BESALCO' THEN   192
                WHEN zc.Codigo_Ins = 'BLUMAR' THEN  193
                WHEN zc.Codigo_Ins = 'BSANTANDER' THEN  194
                WHEN zc.Codigo_Ins = 'CAMANCHACA' THEN  195
                WHEN zc.Codigo_Ins = 'CAP' THEN   196
                WHEN zc.Codigo_Ins = 'CCU' THEN   197
                WHEN zc.Codigo_Ins = 'CEMENTOS' THEN  198
                WHEN zc.Codigo_Ins = 'CENCOSUD' THEN  199
                WHEN zc.Codigo_Ins = 'CHILE' THEN   200
                WHEN zc.Codigo_Ins = 'CMPC' THEN  201
                WHEN zc.Codigo_Ins = 'COLBUN' THEN  202
                WHEN zc.Codigo_Ins = 'CONCHATORO' THEN  203
                WHEN zc.Codigo_Ins = 'COPEC' THEN   204
                WHEN zc.Codigo_Ins = 'CRISTALES' THEN   205
                WHEN zc.Codigo_Ins = 'CTC-A' THEN   206
                WHEN zc.Codigo_Ins = 'ECL' THEN   207
                WHEN zc.Codigo_Ins = 'EMBONOR-B' THEN   208
                WHEN zc.Codigo_Ins = 'ENJOY' THEN   209
                WHEN zc.Codigo_Ins = 'ENTEL' THEN   210
                WHEN zc.Codigo_Ins = 'FALABELLA' THEN   211
                WHEN zc.Codigo_Ins = 'FORUS' THEN   212
                WHEN zc.Codigo_Ins = 'FOSFOROS' THEN  213
                WHEN zc.Codigo_Ins = 'GASCO' THEN   214
                WHEN zc.Codigo_Ins = 'GNCHILE' THEN   215
                WHEN zc.Codigo_Ins = 'HABITAT' THEN   216
                WHEN zc.Codigo_Ins = 'HF' THEN  217
                WHEN zc.Codigo_Ins = 'HITES' THEN   218
                WHEN zc.Codigo_Ins = 'IAM' THEN   219
                WHEN zc.Codigo_Ins = 'IANSA' THEN   220
                WHEN zc.Codigo_Ins = 'ILC' THEN   221
                WHEN zc.Codigo_Ins = 'INDISA' THEN  222
                WHEN zc.Codigo_Ins = 'INTEROCEAN' THEN  223
                WHEN zc.Codigo_Ins = 'ITAUCORP' THEN  224
                WHEN zc.Codigo_Ins = 'NUEVAPOLAR' THEN  225
                WHEN zc.Codigo_Ins = 'LAN' THEN   226
                WHEN zc.Codigo_Ins = 'LTM' THEN   226
                WHEN zc.Codigo_Ins = 'LAS CONDES' THEN  227
                WHEN zc.Codigo_Ins = 'MASISA' THEN  228
                WHEN zc.Codigo_Ins = 'MINERA' THEN  229
                WHEN zc.Codigo_Ins = 'MOLYMET' THEN   230
                WHEN zc.Codigo_Ins = 'MULTIFOODS' THEN  232
                WHEN zc.Codigo_Ins = 'NAVIERA' THEN   233
                WHEN zc.Codigo_Ins = 'NUEVAPOLAR' THEN  234
                WHEN zc.Codigo_Ins = 'PARAUCO' THEN   235
                WHEN zc.Codigo_Ins = 'PAZ' THEN   236
                WHEN zc.Codigo_Ins = 'PEHUENCHE' THEN   237
                WHEN zc.Codigo_Ins = 'PILMAIQUEN' THEN  238
                WHEN zc.Codigo_Ins = 'PROVIDA' THEN   239
                WHEN zc.Codigo_Ins = 'PUCOBRE-A' THEN   240
                WHEN zc.Codigo_Ins = 'RIPLEY' THEN  241
                WHEN zc.Codigo_Ins = 'SALFACORP' THEN   242
                WHEN zc.Codigo_Ins = 'SECURITY' THEN  243
                WHEN zc.Codigo_Ins = 'SK' THEN  244
                WHEN zc.Codigo_Ins = 'SMSAAM' THEN  245
                WHEN zc.Codigo_Ins = 'SOCOVESA' THEN  246
                WHEN zc.Codigo_Ins = 'SONDA' THEN   247
                WHEN zc.Codigo_Ins = 'SQM-B' THEN   248
                WHEN zc.Codigo_Ins = 'VAPORES' THEN   250
                WHEN zc.Codigo_Ins = 'VOLCAN' THEN  251
                WHEN zc.Codigo_Ins = 'VSPT' THEN  252
                WHEN zc.Codigo_Ins = 'WATTS' THEN   253
                WHEN zc.Codigo_Ins = 'ZOFRI' THEN   254
                WHEN zc.Codigo_Ins = 'ENELCHILE' THEN   255
                WHEN zc.Codigo_Ins = 'ENELGXCH' THEN  256
                WHEN zc.Codigo_Ins = 'ENERSIS-AM' THEN  257
                WHEN zc.Codigo_Ins = 'SM-CHILE B' THEN  258
                WHEN zc.Codigo_Ins = 'QUINENCO' THEN  259
                WHEN zc.Codigo_Ins = 'ENDESA-AM' THEN  260
                WHEN zc.Codigo_Ins = 'LIPIGAS' THEN  261
                WHEN zc.codigo_ins = 'ENELAM' THEN 257
                WHEN zc.codigo_ins = 'SMU' THEN 438
                WHEN zc.codigo_ins = 'ORO BLANCO' THEN 460
                WHEN zc.codigo_ins = 'TRICOT' THEN 510
                WHEN zc.codigo_ins = 'EISA' THEN 524
        --BONOS LATAM
           END 
         WHEN zc.moneda = 'UF' THEN   -- Mapping para bonos reajustables
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
              WHEN zc.moneda = 'US$' THEN   -- Mapping para bonos latam
        CASE
                        WHEN zc.codigo_ins = 'AESGEN0529' THEN 264
                        WHEN zc.codigo_ins = 'AESGEN0821' THEN 265
                        WHEN zc.codigo_ins = 'AF241469' THEN 266
                        WHEN zc.codigo_ins = 'AH007884' THEN 267
                        WHEN zc.codigo_ins = 'ALFAA0324 ' THEN 268
                        WHEN zc.codigo_ins = 'ALPEKA0823' THEN 269
                        WHEN zc.codigo_ins = 'AUPIST0622' THEN 270
                        WHEN zc.codigo_ins = 'BANGAN0425' THEN 271
                        WHEN zc.codigo_ins = 'BBVASM0922' THEN 272
                        WHEN zc.codigo_ins = 'BCENC0121 ' THEN 273
                        WHEN zc.codigo_ins = 'BCOCPE0929' THEN 274
                        WHEN zc.codigo_ins = 'BCOLO0621 ' THEN 275
                        WHEN zc.codigo_ins = 'BCP1019   ' THEN 276
                        WHEN zc.codigo_ins = 'BINTPE1020' THEN 277
                        WHEN zc.codigo_ins = 'BRFGMB0926' THEN 278
                        WHEN zc.codigo_ins = 'BRFSBZ0524' THEN 279
                        WHEN zc.codigo_ins = 'CALLAO0423' THEN 280
                        WHEN zc.codigo_ins = 'CDEL0925  ' THEN 281
                        WHEN zc.codigo_ins = 'CENSUD0225' THEN 282
                        WHEN zc.codigo_ins = 'CFELEC0227' THEN 283
                        WHEN zc.codigo_ins = 'CMPCCI1918' THEN 284
                        WHEN zc.codigo_ins = 'CMPCCI2204' THEN 285
                        WHEN zc.codigo_ins = 'COFIDE0729' THEN 286
                        WHEN zc.codigo_ins = 'CORJRL1121' THEN 287
                        WHEN zc.codigo_ins = 'DAVIVI0118' THEN 288
                        WHEN zc.codigo_ins = 'EC642125' THEN 289
                        WHEN zc.codigo_ins = 'ECLCI0125 ' THEN 290
                        WHEN zc.codigo_ins = 'ECOPET0626' THEN 291
                        WHEN zc.codigo_ins = 'ECOPET0923' THEN 292
                        WHEN zc.codigo_ins = 'ED286407' THEN 293
                        WHEN zc.codigo_ins = 'ED825356' THEN 294
                        WHEN zc.codigo_ins = 'EF068792' THEN 295
                        WHEN zc.codigo_ins = 'PCU0735' THEN 296
                        WHEN zc.codigo_ins = 'EF861855' THEN 297
                        WHEN zc.codigo_ins = 'EG945302' THEN 298
                        WHEN zc.codigo_ins = 'EG975321' THEN 299
                        WHEN zc.codigo_ins = 'EG975325' THEN 300
                        WHEN zc.codigo_ins = 'EH468926' THEN 301
                        WHEN zc.codigo_ins = 'ECOPET0719' THEN 302
                        WHEN zc.codigo_ins = 'EH967599' THEN 303
                        WHEN zc.codigo_ins = 'EI015295' THEN 304
                        WHEN zc.codigo_ins = 'EI032072' THEN 305
                        WHEN zc.codigo_ins = 'EI036018' THEN 306
                        WHEN zc.codigo_ins = 'EI054931' THEN 307
                        WHEN zc.codigo_ins = 'EI112049' THEN 308
                        WHEN zc.codigo_ins = 'TELVIS0140' THEN 309
                        WHEN zc.codigo_ins = 'EI213380' THEN 310
                        WHEN zc.codigo_ins = 'EI213384' THEN 311
                        WHEN zc.codigo_ins = 'EI241890' THEN 312
                        WHEN zc.codigo_ins = 'EI306294' THEN 313
                        WHEN zc.codigo_ins = 'EI327873' THEN 314
                        WHEN zc.codigo_ins = 'EI336211' THEN 315
                        WHEN zc.codigo_ins = 'AMXLMM0340' THEN 316
                        WHEN zc.codigo_ins = 'EI336243' THEN 317
                        WHEN zc.codigo_ins = 'EI349086' THEN 318
                        WHEN zc.codigo_ins = 'EI400317' THEN 319
                        WHEN zc.codigo_ins = 'BCP0920' THEN 320
                        WHEN zc.codigo_ins = 'EI419310' THEN 321
                        WHEN zc.codigo_ins = 'EI467009' THEN 322
                        WHEN zc.codigo_ins = 'EI507822' THEN 323
                        WHEN zc.codigo_ins = 'EI600528' THEN 324
                        WHEN zc.codigo_ins = 'EI627254' THEN 325
                        WHEN zc.codigo_ins = 'EI637624' THEN 326
                        WHEN zc.codigo_ins = 'EI675437' THEN 328
                        WHEN zc.codigo_ins = 'EI757014' THEN 329
                        WHEN zc.codigo_ins = 'EI810168' THEN 330
                        WHEN zc.codigo_ins = 'EI868226' THEN 331
                        WHEN zc.codigo_ins = 'EI939724' THEN 332
                        WHEN zc.codigo_ins = 'EI992536' THEN 333
                        WHEN zc.codigo_ins = 'EJ123001' THEN 334
                        WHEN zc.codigo_ins = 'EJ141226' THEN 335
                        WHEN zc.codigo_ins = 'EJ152916' THEN 336
                        WHEN zc.codigo_ins = 'EJ237099' THEN 337
                        WHEN zc.codigo_ins = 'EJ247759' THEN 338
                        WHEN zc.codigo_ins = 'EJ276737' THEN 339
                        WHEN zc.codigo_ins = 'EJ276742' THEN 340
                        WHEN zc.codigo_ins = 'BCOCPE0822' THEN 341
                        WHEN zc.codigo_ins = 'EJ341555' THEN 342
                        WHEN zc.codigo_ins = 'EJ341560' THEN 343
                        WHEN zc.codigo_ins = 'EJ350241' THEN 344
                        WHEN zc.codigo_ins = 'BSANCI0922' THEN 345
                        WHEN zc.codigo_ins = 'EJ363274' THEN 346
                        WHEN zc.codigo_ins = 'EJ393172' THEN 347
                        WHEN zc.codigo_ins = 'BSANTM1122' THEN 348
                        WHEN zc.codigo_ins = 'EJ447299' THEN 349
                        WHEN zc.codigo_ins = 'CENSUD0123' THEN 350
                        WHEN zc.codigo_ins = 'GMEXIB1232' THEN 351
                        WHEN zc.codigo_ins = 'EJ501005' THEN 352
                        WHEN zc.codigo_ins = 'EJ548869' THEN 353
                        WHEN zc.codigo_ins = 'EJ609917' THEN 354
                        WHEN zc.codigo_ins = 'EJ611543' THEN 355
                        WHEN zc.codigo_ins = 'EJ621340' THEN 356
                        WHEN zc.codigo_ins = 'EJ627590' THEN 357
                        WHEN zc.codigo_ins = 'TGPERU0428' THEN 358
                        WHEN zc.codigo_ins = 'EJ654229' THEN 359
                        WHEN zc.codigo_ins = 'EJ668899' THEN 360
                        WHEN zc.codigo_ins = 'EJ668914' THEN 361
                        WHEN zc.codigo_ins = 'EJ671705' THEN 362
                        WHEN zc.codigo_ins = 'EJ682987' THEN 363
                        WHEN zc.codigo_ins = 'EJ767592' THEN 364
                        WHEN zc.codigo_ins = 'EJ828279' THEN 365
                        WHEN zc.codigo_ins = 'ECOPET0943' THEN 366
                        WHEN zc.codigo_ins = 'EJ836618' THEN 367
                        WHEN zc.codigo_ins = 'EJ858949' THEN 368
                        WHEN zc.codigo_ins = 'FRESLN1123' THEN 369
                        WHEN zc.codigo_ins = 'EJ948876' THEN 370
                        WHEN zc.codigo_ins = 'EJ948900' THEN 371
                        WHEN zc.codigo_ins = 'EJ948972' THEN 372
                        WHEN zc.codigo_ins = 'EK032439' THEN 373
                        WHEN zc.codigo_ins = 'EK044884' THEN 374
                        WHEN zc.codigo_ins = 'MINSUR0224' THEN 375
                        WHEN zc.codigo_ins = 'EK141014' THEN 376
                        WHEN zc.codigo_ins = 'EK164157' THEN 377
                        WHEN zc.codigo_ins = 'EK165147' THEN 378
                        WHEN zc.codigo_ins = 'EK172187' THEN 379
                        WHEN zc.codigo_ins = 'EK174265' THEN 380
                        WHEN zc.codigo_ins = 'EK244336' THEN 381
                        WHEN zc.codigo_ins = 'EK254004' THEN 382
                        WHEN zc.codigo_ins = 'EK265161' THEN 383
                        WHEN zc.codigo_ins = 'ECOPET0545' THEN 384
                        WHEN zc.codigo_ins = 'EK306386' THEN 385
                        WHEN zc.codigo_ins = 'EK352999' THEN 386
                        WHEN zc.codigo_ins = 'EK353005' THEN 387
                        WHEN zc.codigo_ins = 'EK366169' THEN 388
                        WHEN zc.codigo_ins = 'EK379309' THEN 389
                        WHEN zc.codigo_ins = 'ENTEL0826' THEN 390
                        WHEN zc.codigo_ins = 'EK483779' THEN 391
                        WHEN zc.codigo_ins = 'EK485153' THEN 392
                        WHEN zc.codigo_ins = 'EK487687' THEN 393
                        WHEN zc.codigo_ins = 'EK499474' THEN 394
                        WHEN zc.codigo_ins = 'EK518163' THEN 395
                        WHEN zc.codigo_ins = 'EK563949' THEN 396
                        WHEN zc.codigo_ins = 'EK568142' THEN 397
                        WHEN zc.codigo_ins = 'GRUMAB1224' THEN 398
                        WHEN zc.codigo_ins = 'EK741346' THEN 399
                        WHEN zc.codigo_ins = 'EK870984' THEN 400
                        WHEN zc.codigo_ins = 'EK892807' THEN 401
                        WHEN zc.codigo_ins = 'EK901418' THEN 402
                        WHEN zc.codigo_ins = 'EK951278' THEN 403
                        WHEN zc.codigo_ins = 'EK964786' THEN 404
                        WHEN zc.codigo_ins = 'LIMAMT0734' THEN 405
                        WHEN zc.codigo_ins = 'ENAPCL0826' THEN 406
                        WHEN zc.codigo_ins = 'ENAPCL1024' THEN 407
                        WHEN zc.codigo_ins = 'ENRSIS1026' THEN 408
                        WHEN zc.codigo_ins = 'ENTEL3024 ' THEN 409
                        WHEN zc.codigo_ins = 'FERMAC0338' THEN 410
                        WHEN zc.codigo_ins = 'FIBRBZ0127' THEN 411
                        WHEN zc.codigo_ins = 'FUNOTR1224' THEN 412
                        WHEN zc.codigo_ins = 'GGBRB0121 ' THEN 413
                        WHEN zc.codigo_ins = 'GLBACO1019' THEN 414
                        WHEN zc.codigo_ins = 'GLBACO1021' THEN 415
                        WHEN zc.codigo_ins = 'GNLQCI0729' THEN 416
                        WHEN zc.codigo_ins = 'GRUPOS0426' THEN 417
                        WHEN zc.codigo_ins = 'KALLPA0526' THEN 418
                        WHEN zc.codigo_ins = 'LIVEPL1026' THEN 419
                        WHEN zc.codigo_ins = 'LW371842' THEN 420
                        WHEN zc.codigo_ins = 'LW810722' THEN 421
                        WHEN zc.codigo_ins = 'MEXCAT1026' THEN 422
                        WHEN zc.codigo_ins = 'MXCHF0922 ' THEN 423
                        WHEN zc.codigo_ins = 'OCENSA0521' THEN 424
                        WHEN zc.codigo_ins = 'TERRAF1122' THEN 425
                        WHEN zc.codigo_ins = 'QJ878935' THEN 426
                        WHEN zc.codigo_ins = 'QJ879027' THEN 427
                        WHEN zc.codigo_ins = 'VALEBZ0826' THEN 428
                        WHEN zc.codigo_ins = 'RAIZBZ0127' THEN 429
                        WHEN zc.codigo_ins = 'SCCO0425  ' THEN 430
                        WHEN zc.codigo_ins = 'SIGMA0526 ' THEN 431
                        WHEN zc.codigo_ins = 'SUAMSA0424' THEN 432
                        WHEN zc.codigo_ins = 'TANNER0318' THEN 433
                        WHEN zc.codigo_ins = 'TRAGSA0322' THEN 434
                        WHEN zc.codigo_ins = 'TRANSM0523' THEN 435
                        WHEN zc.codigo_ins = 'MIVIVI0123' THEN 436
                        WHEN zc.codigo_ins = 'EMBRBZ0227' THEN 461
                        WHEN zc.codigo_ins = 'EJ997555' THEN 446
                        WHEN zc.codigo_ins = 'CMPCCI0427' THEN 474
                        WHEN zc.codigo_ins = 'SUAMSA0427' THEN 475
                        WHEN zc.codigo_ins = 'BINBUR0427' THEN 476
                        WHEN zc.codigo_ins = 'CDEL0722' THEN 477
                        WHEN zc.codigo_ins in ('TREA033122', 'TREA053122') THEN 478
                        WHEN zc.codigo_ins = 'CELEO 0647' THEN 486
                        WHEN zc.codigo_ins = 'CFELEC0124' THEN 488
                        WHEN zc.codigo_ins = 'GLOPAR0327' THEN 489
                        WHEN zc.codigo_ins = 'LATAIR1127' THEN 498
                        WHEN zc.codigo_ins = 'SQM0125' THEN 500
                        WHEN zc.codigo_ins = 'SQM0420' THEN 501
                        WHEN zc.codigo_ins = 'MXCHF1119' THEN 502
                        WHEN zc.codigo_ins = 'PETRPE0632' THEN 503
                        WHEN zc.codigo_ins = 'CENSUD0727' THEN 504
                        WHEN zc.codigo_ins = 'SUZANO0726' THEN 505
                        WHEN zc.codigo_ins = 'BANBOG0827' THEN 507
                        WHEN zc.codigo_ins = 'BANGEN0827' THEN 508
                        WHEN zc.codigo_ins = 'KALLPA0827' THEN 509
                        WHEN zc.codigo_ins = 'PEMEX0327' THEN 511
                        WHEN zc.codigo_ins = 'SUZANO1426' THEN 512
                        WHEN zc.codigo_ins = 'BISTPP0922' THEN 513
                        WHEN zc.codigo_ins = 'AEIUS0927' THEN 514
                        WHEN zc.codigo_ins = 'MEXCAT0428' THEN 515
                        WHEN zc.codigo_ins = 'MEXCAT0747' THEN 516
                        WHEN zc.codigo_ins = 'MXCHF1027' THEN 517
                        WHEN zc.codigo_ins = 'MXCHF0148' THEN 518
                        WHEN zc.codigo_ins = 'BRASKM0123' THEN 519
                        WHEN zc.codigo_ins = 'BRASKM0128' THEN 520
                        WHEN zc.codigo_ins = 'COLBUN1027' THEN 521
                        WHEN zc.codigo_ins = 'GGBRBZ1027' THEN 522
                        WHEN zc.codigo_ins = 'INTFSI1027' THEN 523
                        WHEN zc.codigo_ins = 'BFALA1027' THEN 525
                        WHEN zc.codigo_ins = 'CELARA1127' THEN 526
                        WHEN zc.codigo_ins = 'MULT1122' THEN 529
                        WHEN zc.codigo_ins = 'AP450922' THEN 530
                        WHEN zc.codigo_ins = 'FIBRBZ0125' THEN 531

                END
       END
           AS Index_Id, emisores.sector AS sector, zc.riesgo as riesgo_internacional, emisores.Pais_Emisor as pais_emisor, emisores.nombre_emisor as nombre_emisor
FROM   [MesaInversiones].[dbo].[zhis_carteras_bmk] zc 
left outer join instrumentos
ON zc.Codigo_Ins = Instrumentos.Codigo_Ins
left outer join emisores
on instrumentos.codigo_emi = emisores.codigo_emi
left outer join Fondos_Benchmark benchmarks
on zc.benchmark_id = benchmarks.benchmark_id
left outer join FondosIR f
on benchmarks.codigo_fdo = f.codigo_fdo
WHERE  zc.fecha = 'AUTODATE' AND zc.benchmark_id = AUTOBMK



