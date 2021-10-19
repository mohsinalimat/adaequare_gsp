data_eway_gen = {
    "supplyType":"O",
    "subSupplyType":"1",
    "docType":"INV",
    "docNo":"123-853426dd",
    "docDate":"15/12/2017",
    "fromGstin":"05AAACG2115R1ZN",
    "fromTrdName":"welton",
    "fromAddr1":"2ND CROSS NO 59  19  A",
    "fromAddr2":"GROUND FLOOR OSBORNE ROAD",
    "fromPlace":"FRAZER TOWN",
    "fromPincode":560042,
    "actFromStateCode":29,"fromStateCode":29,
    "transactionType": 1,
    "toGstin":"05AAACG2140A1ZL",
    "toTrdName":"sthuthya",
    "toAddr1":"Shree Nilaya",
    "toAddr2":"Dasarahosahalli",
    "toPlace":"Beml Nagar",
    "toPincode":560042,
    "actToStateCode":29,
    "toStateCode":29,
    "totalValue":5609889,
    "cgstValue":336593.34,
    "sgstValue":336593.34,
    "igstValue":0,
    "cessValue":0,
    "totInvValue":6283075.68,
    "transporterId":"",
    "transporterName":"",
    "transDocNo":"",
    "transMode":"1",
    "transDistance":"25",
    "transDocDate":"",
    "vehicleNo":"PVC1234",
    "vehicleType":"R",
    "itemList":
    [{
    "productName":"Wheat",
    "productDesc":"Wheat",
    "hsnCode":1001,
    "quantity":4,
    "qtyUnit":"BOX",
    "cgstRate":6,
    "sgstRate":6,
    "igstRate":0,
    "cessRate":0,
    "cessAdvol":0,
    "taxableAmount":5609889
    }
    ]}

update_vehicle = {
  "EwbNo": 381002748764,
  "VehicleNo": "PQR9876",
  "FromPlace": "BANGALORE",
  "FromState": 29,
 "ReasonCode": "1",
  "ReasonRem": "vehicle broke down",
   "TransMode": "1"
}

extend_validity = {
"ewbNo": 381002748764,
"vehicleNo": "HR04EL1234",
"fromPlace":"Bengaluru",
"fromStateCode":6,
"fromState":6,
"frompincode": 133001,
"remainingDistance":25,
"consignmentStatus":"M",
"transitType":"",
"transDocNo": "1234 ",
"transDocDate": "26/04/2019",
"transMode": "1",
"extnRsnCode":1,
"extnRemarks":"Flood"
}

update_transporter = {
"ewbNo":"321002748737",
"transporterId":"29AKLPM8755F1Z2"
}

cancel = {
"ewbNo": "331002748800",
 "cancelRsnCode": 2
}