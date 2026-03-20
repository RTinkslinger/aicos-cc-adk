#!/usr/bin/env python3
"""Fetch Notion page body content for companies O-Z and save as markdown."""

import json
import os
import re
import time
import requests

NOTION_TOKEN = "os.environ.get("NOTION_TOKEN", "")"
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"
OUTPUT_DIR = "/Users/Aakash/Claude Projects/Aakash AI CoS CC ADK/companies-pages"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

# Companies O-Z from the database query
COMPANIES = [
    {"id": 312, "name": "O21 Capital", "notion_page_id": "31dbe9ad-7f96-4b24-ad46-893a15e2ec76"},
    {"id": 313, "name": "Obvious Finance", "notion_page_id": "7734f1ff-fabf-46fc-a2f9-a9746545e972"},
    {"id": 314, "name": "OfScale", "notion_page_id": "ad856fdf-894c-4828-acf9-731c2226284e"},
    {"id": 315, "name": "OhSoGo", "notion_page_id": "a49ffd87-be66-4b65-8f49-11fc8587a725"},
    {"id": 316, "name": "Oji Cabs", "notion_page_id": "a66dcfc6-935c-4193-a505-92867827145b"},
    {"id": 317, "name": "Olive (YC W25)", "notion_page_id": "23e29bcc-b6fc-808c-8f79-f06b2bc6f0f4"},
    {"id": 318, "name": "OnCall Owl", "notion_page_id": "27b29bcc-b6fc-805b-884a-c4f7e655853a"},
    {"id": 319, "name": "OnCare", "notion_page_id": "2d6e370c-36a0-4625-b0fd-56d73e75e2d7"},
    {"id": 599, "name": "One Impression", "notion_page_id": "3cb08975-692f-4592-90de-32f55edc32c4"},
    {"id": 320, "name": "OnFinance AI", "notion_page_id": "d53c8a3c-d70d-479e-b7f4-d31a37b9dc1d"},
    {"id": 321, "name": "Operators Studio", "notion_page_id": "25029bcc-b6fc-8020-89ac-ee415bc83665"},
    {"id": 322, "name": "Opsera", "notion_page_id": "32629bcc-b6fc-8184-a430-ccf806e7fade"},
    {"id": 323, "name": "OpusCollect", "notion_page_id": "2e229bcc-b6fc-819a-a211-cedd85e6a7b6"},
    {"id": 324, "name": "Orange Slice", "notion_page_id": "22529bcc-b6fc-81d2-b329-e06af7f061c1"},
    {"id": 325, "name": "Orbi", "notion_page_id": "30a29bcc-b6fc-814c-95e0-e8eb46cd967a"},
    {"id": 326, "name": "Orbit Farming", "notion_page_id": "19431912-4e09-4cbb-a834-9bf7bd3ea614"},
    {"id": 327, "name": "Orbit Wallet", "notion_page_id": "11529bcc-b6fc-80f9-92de-db436ab9abee"},
    {"id": 328, "name": "Origin", "notion_page_id": "32629bcc-b6fc-815c-a269-ff59d72e5ce6"},
    {"id": 329, "name": "Origin Bio", "notion_page_id": "31529bcc-b6fc-80b1-9915-d9216c958adf"},
    {"id": 330, "name": "Oximy", "notion_page_id": "32729bcc-b6fc-8123-b686-f320454a76aa"},
    {"id": 331, "name": "Pactle", "notion_page_id": "31c29bcc-b6fc-8102-bde6-dff7d17cd08a"},
    {"id": 332, "name": "Padel India", "notion_page_id": "fde22137-79d7-407b-b8bc-06f4e27b2451"},
    {"id": 333, "name": "Pallav Singh's new company", "notion_page_id": "9cc824f6-e78b-4270-880c-4aa992b64a1f"},
    {"id": 334, "name": "Paradigm Shift Capital", "notion_page_id": "1bf80938-a5e9-4dcf-9b65-8924d866b19d"},
    {"id": 335, "name": "Patcorn", "notion_page_id": "852f6604-d6b2-4093-82a0-c003722d9b94"},
    {"id": 336, "name": "Patronus", "notion_page_id": "4e3b67c1-58f9-4c52-9ca3-570930b7b5d8"},
    {"id": 337, "name": "Payso (acq. MSwipe)", "notion_page_id": "13c29bcc-b6fc-80d9-a9a2-e67ca4cadbf5"},
    {"id": 338, "name": "Peace Vault", "notion_page_id": "2e129bcc-b6fc-81ac-8608-d888935d12d0"},
    {"id": 339, "name": "Peak Health", "notion_page_id": "15129bcc-b6fc-80bb-aa7f-e2c16bd46c25"},
    {"id": 340, "name": "PeakXV (f.k.a Sequoia Capital India)", "notion_page_id": "dbee2c0d-cb4f-4c72-a87d-aa6dcbb1abc2"},
    {"id": 341, "name": "Pear VC", "notion_page_id": "20029bcc-b6fc-8065-b65d-dd50b2b3c3ad"},
    {"id": 342, "name": "Performance Trust Capital Partners", "notion_page_id": "22529bcc-b6fc-81b5-ab77-d996cf91c597"},
    {"id": 343, "name": "PhonePe", "notion_page_id": "eb95d281-f81c-4758-b26a-5fa516df5353"},
    {"id": 344, "name": "Pinegap AI", "notion_page_id": "cd6be8e0-831e-46a6-b2f3-1a0779f95271"},
    {"id": 345, "name": "Pixie", "notion_page_id": "30429bcc-b6fc-8165-8e9c-ca9aa6888022"},
    {"id": 346, "name": "Pleom", "notion_page_id": "22c29bcc-b6fc-81c7-8c83-d14352e029f7"},
    {"id": 347, "name": "Poised", "notion_page_id": "56fbb134-dc4c-4dc0-bd36-0c3709a2b536"},
    {"id": 348, "name": "Pokus", "notion_page_id": "2b229bcc-b6fc-8037-896a-e0443fa8ceea"},
    {"id": 349, "name": "Polopan", "notion_page_id": "31429bcc-b6fc-811a-9559-fdaf11e0599f"},
    {"id": 350, "name": "Polymorph", "notion_page_id": "32629bcc-b6fc-8125-91c3-c847551aa346"},
    {"id": 351, "name": "Polymorph", "notion_page_id": "32629bcc-b6fc-8186-9daa-f0ed11a851cc"},
    {"id": 352, "name": "Polymorph (YC W26)", "notion_page_id": "32629bcc-b6fc-8194-8d51-c9b1403ba2c1"},
    {"id": 600, "name": "Polytrade", "notion_page_id": "6d6b5ac6-842b-467f-bfd3-a41f07381847"},
    {"id": 353, "name": "Pond", "notion_page_id": "22d29bcc-b6fc-80ac-877d-d9cd0deb2a9e"},
    {"id": 354, "name": "Port", "notion_page_id": "1e829bcc-b6fc-805c-a8b1-e40997ff8fc3"},
    {"id": 355, "name": "Potpie", "notion_page_id": "1f229bcc-b6fc-80da-8870-f06609cd08ce"},
    {"id": 356, "name": "PowerEdge", "notion_page_id": "17e29bcc-b6fc-8037-bf9e-d31bd5afbfad"},
    {"id": 357, "name": "PowerUp", "notion_page_id": "18429bcc-b6fc-8074-9135-da40cec9b074"},
    {"id": 358, "name": "Prabhkiran's new company", "notion_page_id": "11f29bcc-b6fc-80dc-9c29-df47d8fb87ee"},
    {"id": 359, "name": "Pranay's new company", "notion_page_id": "1ee29bcc-b6fc-80e2-b3c1-d9a9a725e372"},
    {"id": 360, "name": "Pravah", "notion_page_id": "1e729bcc-b6fc-805f-b5d7-ec0494bce9f3"},
    {"id": 361, "name": "Pre6 AI", "notion_page_id": "22f29bcc-b6fc-8010-8824-d67c21e1db5f"},
    {"id": 362, "name": "ProactAI", "notion_page_id": "30c29bcc-b6fc-818e-bb5d-d76682e15b30"},
    {"id": 363, "name": "Promaft Partners", "notion_page_id": "b7564322-b4c4-4190-aa3b-e3a12cce4910"},
    {"id": 364, "name": "Promaft Partners", "notion_page_id": "d4097d53-9d44-4831-aa5c-bbf92227560f"},
    {"id": 365, "name": "Propel", "notion_page_id": "17629bcc-b6fc-802e-acf0-d94e45272987"},
    {"id": 366, "name": "PropelPro (Dimensionless Tech)", "notion_page_id": "de3f2444-b3f8-4e1a-b3d5-ace8150d1114"},
    {"id": 367, "name": "Prosparity", "notion_page_id": "e5c29f78-7116-49df-9196-9b7c9b3626b4"},
    {"id": 368, "name": "Prosperity7 Ventures", "notion_page_id": "5c64f7e6-377b-480c-a5b0-b3a7848523fc"},
    {"id": 369, "name": "Prosphor Capital", "notion_page_id": "25029bcc-b6fc-8007-ba1a-ce062a932603"},
    {"id": 370, "name": "Protent", "notion_page_id": "32629bcc-b6fc-817e-9b0f-e96877dd12da"},
    {"id": 371, "name": "Proton Health", "notion_page_id": "1c529bcc-b6fc-80a0-9cc9-f07dbe840ece"},
    {"id": 372, "name": "PruVen Capital", "notion_page_id": "1f529bcc-b6fc-804d-84e9-ed152e82405b"},
    {"id": 373, "name": "Puch AI (f.k.a. TurboML)", "notion_page_id": "46faa35d-45fc-43a6-9df7-ebce678b0f48"},
    {"id": 374, "name": "Puneet Singh (ex-Simpl CTO) — stealth", "notion_page_id": "31329bcc-b6fc-811b-a01f-eb4c5d300571"},
    {"id": 375, "name": "PyEnvManager", "notion_page_id": "2e029bcc-b6fc-8125-971e-fd8498f01d25"},
    {"id": 376, "name": "Qatalog", "notion_page_id": "b4a86559-95d4-496a-b578-82f6c627b89f"},
    {"id": 377, "name": "Qila", "notion_page_id": "3686c2fd-1bee-438d-aabf-157e175eee27"},
    {"id": 378, "name": "Qodex AI", "notion_page_id": "1c329bcc-b6fc-8085-9410-eba29146f514"},
    {"id": 379, "name": "Quash Bugs", "notion_page_id": "b129417f-edf5-4434-b03d-0a5907d480d6"},
    {"id": 380, "name": "Quivly", "notion_page_id": "28b29bcc-b6fc-80f1-8b51-c98883d8690c"},
    {"id": 601, "name": "Qwik Build (f.k.a Snowmountain)", "notion_page_id": "7e086baf-e130-4405-84cb-d8f531bcba14"},
    {"id": 381, "name": "Qwikly", "notion_page_id": "32829bcc-b6fc-81fa-bfbe-d56f2d2ace97"},
    {"id": 382, "name": "RagaAI", "notion_page_id": "31229bcc-b6fc-8180-bbd2-eefb584613f6"},
    {"id": 383, "name": "Rahul Tarak's Company", "notion_page_id": "22b29bcc-b6fc-81b7-a1cb-e348bd00eaa6"},
    {"id": 384, "name": "Rakshan AI", "notion_page_id": "27429bcc-b6fc-8106-a367-e76764637827"},
    {"id": 385, "name": "Ram J's new company", "notion_page_id": "22d29bcc-b6fc-8030-8f77-cf2e91b45c7e"},
    {"id": 386, "name": "Rankly", "notion_page_id": "30429bcc-b6fc-81b6-bed7-e86e01997300"},
    {"id": 387, "name": "RapidClaims", "notion_page_id": "1eea9c4b-38a0-4249-bbfc-206f700453ce"},
    {"id": 388, "name": "Rarebase", "notion_page_id": "0dd96752-bd98-4279-a201-7b5945ce1384"},
    {"id": 389, "name": "Ravesh's company", "notion_page_id": "22d29bcc-b6fc-80b1-a09b-c6975ea375e6"},
    {"id": 390, "name": "Realiti.io", "notion_page_id": "c2e85be0-21b8-4dc1-9aaf-29b26881e47e"},
    {"id": 391, "name": "Recrew AI (f.k.a. Gloroots)", "notion_page_id": "8528c314-63b5-454d-b44b-d6a2d8e95d11"},
    {"id": 392, "name": "Remus Capital", "notion_page_id": "23829bcc-b6fc-80f3-99b4-eb7826eeba5c"},
    {"id": 393, "name": "Renderwolf", "notion_page_id": "babb07c9-f181-44db-a5ad-99b733eb8abf"},
    {"id": 394, "name": "Repaio", "notion_page_id": "1c829bcc-b6fc-80dc-93f7-cb76939c95d3"},
    {"id": 395, "name": "ReplyAll (PRBT)", "notion_page_id": "16129bcc-b6fc-809b-9802-e1b8ba4578f1"},
    {"id": 396, "name": "Resolvd AI", "notion_page_id": "32629bcc-b6fc-8136-8865-dd97a9e8aeff"},
    {"id": 397, "name": "Returns (f.k.a. Optionbase)", "notion_page_id": "792a52a6-46fe-4921-8011-99bfe65b9c56"},
    {"id": 398, "name": "Revenoid", "notion_page_id": "18929bcc-b6fc-80a8-acfc-c9eff844aae3"},
    {"id": 399, "name": "Revspot.AI", "notion_page_id": "902f3587-e9e4-4deb-b3bb-96f9e8ec9f5b"},
    {"id": 400, "name": "Rezolv", "notion_page_id": "13629bcc-b6fc-801c-aea2-f946593702b3"},
    {"id": 401, "name": "Rhym", "notion_page_id": "12029bcc-b6fc-80bd-b1f3-f842836977b4"},
    {"id": 402, "name": "Rhym", "notion_page_id": "471fa3e2-8b04-495f-8aad-c86893afca2a"},
    {"id": 403, "name": "Ribbit Capital", "notion_page_id": "25a29bcc-b6fc-81bd-bd97-c26b918fa6da"},
    {"id": 404, "name": "Rilo (f.k.a. Workatoms)", "notion_page_id": "27029bcc-b6fc-80ce-8837-de3ec875e7dc"},
    {"id": 405, "name": "Riverbank", "notion_page_id": "22529bcc-b6fc-81eb-a01d-e0e254227b50"},
    {"id": 406, "name": "Riverline (f.k.a Recontact)", "notion_page_id": "1af29bcc-b6fc-80f4-876b-edc70ab57af9"},
    {"id": 407, "name": "Riverstone Capital", "notion_page_id": "27a29bcc-b6fc-80df-a8ad-e84affa4eefc"},
    {"id": 408, "name": "Rizzle", "notion_page_id": "11129bcc-b6fc-80cc-ab3f-e7537f887fb6"},
    {"id": 409, "name": "Rotation Capital", "notion_page_id": "fff29bcc-b6fc-8061-8edb-d90fba510980"},
    {"id": 410, "name": "Routines", "notion_page_id": "10d29bcc-b6fc-80dd-9efb-ccb9fc4cc628"},
    {"id": 411, "name": "Roy's VC Fund", "notion_page_id": "1d529bcc-b6fc-8079-95f7-ca7e7b0460ae"},
    {"id": 412, "name": "RTP Ventures", "notion_page_id": "b08fa2e9-2048-4a3e-a36c-2b26c9170ca0"},
    {"id": 413, "name": "RunAnywhere", "notion_page_id": "32629bcc-b6fc-81ef-a9c8-e8ed32654118"},
    {"id": 414, "name": "RunAnywhere (YC W26)", "notion_page_id": "32629bcc-b6fc-81f3-bfff-c0f31f6aab3b"},
    {"id": 415, "name": "Ryvo AI", "notion_page_id": "27829bcc-b6fc-80a2-8eb8-dce3a2cf67a5"},
    {"id": 416, "name": "Saama VC", "notion_page_id": "16029bcc-b6fc-8050-9be4-d111d0d5282e"},
    {"id": 417, "name": "Sai Alisetty's company", "notion_page_id": "22d29bcc-b6fc-80fa-9b8d-c243e7defbd5"},
    {"id": 418, "name": "Saka VC", "notion_page_id": "26a29bcc-b6fc-808a-9c12-d4e8c670d103"},
    {"id": 419, "name": "SalesChat", "notion_page_id": "d4b014c4-c379-40ff-a536-cece4932d20d"},
    {"id": 420, "name": "Samsung R&D Institute India", "notion_page_id": "32729bcc-b6fc-8184-8569-e106020fe9a4"},
    {"id": 421, "name": "Sandeep R's new co", "notion_page_id": "11229bcc-b6fc-8035-95f4-ddf71907cd77"},
    {"id": 422, "name": "Satish & Dhawal's company", "notion_page_id": "22d29bcc-b6fc-8054-b341-c6a30e11d1a1"},
    {"id": 423, "name": "Satish's VC Fund", "notion_page_id": "25029bcc-b6fc-8019-82b2-cf1bc39ef68b"},
    {"id": 424, "name": "Sauce VC", "notion_page_id": "7e13d71e-ab94-41a8-9f97-237669c5e324"},
    {"id": 425, "name": "Savr", "notion_page_id": "30f29bcc-b6fc-81c0-8dee-e413c61368fc"},
    {"id": 426, "name": "Sayfol International School", "notion_page_id": "32629bcc-b6fc-81a0-93fc-fd12998f9fdb"},
    {"id": 427, "name": "Schema Ventures", "notion_page_id": "1d529bcc-b6fc-802e-b61f-c8deadef7515"},
    {"id": 428, "name": "Selkea", "notion_page_id": "20029bcc-b6fc-8028-aaf3-e322a0e05b85"},
    {"id": 429, "name": "Sentrial", "notion_page_id": "32629bcc-b6fc-8185-88cd-dba585040628"},
    {"id": 430, "name": "Serai Homes", "notion_page_id": "4f63ebd8-ea36-4b50-88db-4bf2397b79c5"},
    {"id": 431, "name": "Serendipity Space", "notion_page_id": "1b529bcc-b6fc-8016-9a7a-d9df2fcbee73"},
    {"id": 432, "name": "Seth Anandram Jaipuria School", "notion_page_id": "32629bcc-b6fc-81ec-9006-c7916c339b4b"},
    {"id": 433, "name": "Sharang Shakti Pvt. Ltd.", "notion_page_id": "29e29bcc-b6fc-81e6-b2f8-ea4e54d433b0"},
    {"id": 434, "name": "ShARE - Growing a new generation of leaders", "notion_page_id": "32729bcc-b6fc-8102-b544-fdaf74314934"},
    {"id": 435, "name": "Sheta Mittal's company", "notion_page_id": "db90651b-faf9-4a99-aafe-5a5726e5eb20"},
    {"id": 436, "name": "Shiro", "notion_page_id": "22629bcc-b6fc-8068-a4e7-d594842e5e3d"},
    {"id": 437, "name": "Siff AI", "notion_page_id": "32629bcc-b6fc-8145-80e2-d39c66abc64d"},
    {"id": 438, "name": "Silicon Valley Commerce", "notion_page_id": "32629bcc-b6fc-8181-a0ef-c04318af8118"},
    {"id": 439, "name": "Skydda", "notion_page_id": "1de29bcc-b6fc-8047-8bf2-cf29d85e985f"},
    {"id": 602, "name": "Smallest AI", "notion_page_id": "feaeb55a-f08e-4ea0-8042-9d4485e1f57d"},
    {"id": 440, "name": "SmartSuite", "notion_page_id": "32629bcc-b6fc-81f5-b92c-fec6ed6226d2"},
    {"id": 441, "name": "Solar Ladder", "notion_page_id": "cdcf7069-2276-4f22-84e9-4e6709f89c75"},
    {"id": 442, "name": "Sonarly", "notion_page_id": "32629bcc-b6fc-81dd-bbed-d98383fedcd4"},
    {"id": 443, "name": "Soulside", "notion_page_id": "2f129bcc-b6fc-813f-a3ab-d43ffc9c0ead"},
    {"id": 444, "name": "SpaceFields", "notion_page_id": "921694ce-ac2c-4626-acb6-5bb4e4fc4106"},
    {"id": 445, "name": "Spare8", "notion_page_id": "5f03512a-b4fb-49e6-86c2-06596735cb1c"},
    {"id": 446, "name": "Speciale Invest", "notion_page_id": "9300849f-f862-4c83-a193-b08ba3d34fdb"},
    {"id": 603, "name": "Spheron Network", "notion_page_id": "c0137edc-bec2-40ae-a514-b06ffea06dc3"},
    {"id": 448, "name": "Sponge", "notion_page_id": "32629bcc-b6fc-812c-aee9-cc92db05f137"},
    {"id": 447, "name": "Sponge", "notion_page_id": "32629bcc-b6fc-817c-9097-d34c18190f28"},
    {"id": 449, "name": "Spybird", "notion_page_id": "12029bcc-b6fc-806c-9682-e1efdc267142"},
    {"id": 450, "name": "Spydra", "notion_page_id": "b7558602-8c22-4bf4-9ebe-53f2bc86d910"},
    {"id": 451, "name": "Sriram's company", "notion_page_id": "22d29bcc-b6fc-8055-84fd-c8ad81d6bfe3"},
    {"id": 452, "name": "Stable Address", "notion_page_id": "f04b5b9d-a6ab-4531-814e-d290dcae8bbb"},
    {"id": 453, "name": "Stacksync", "notion_page_id": "32629bcc-b6fc-8123-8a9b-deed329f34e0"},
    {"id": 454, "name": "Stance Health (f.k.a. HealthFlex)", "notion_page_id": "138a5abc-9891-4429-a148-30dced089e47"},
    {"id": 455, "name": "Standard Capital", "notion_page_id": "26329bcc-b6fc-80ed-bbdd-eb1e688109c0"},
    {"id": 456, "name": "Stargazer Fund", "notion_page_id": "28f29bcc-b6fc-80ef-81c9-cd9d98f47726"},
    {"id": 457, "name": "Stealth Startup (Building for Seniors in India)", "notion_page_id": "32829bcc-b6fc-815b-9251-d2273384bd07"},
    {"id": 458, "name": "Stealth Startup (Consumer)", "notion_page_id": "32829bcc-b6fc-815c-86c2-c01d0163b4ac"},
    {"id": 459, "name": "Stellaris Venture Partners", "notion_page_id": "76329264-1559-4b32-a292-6affb2ac25be"},
    {"id": 460, "name": "Stellon Labs", "notion_page_id": "22c29bcc-b6fc-8019-863f-e1faf3b37c44"},
    {"id": 604, "name": "Step Security", "notion_page_id": "bc506ab0-f5f8-43da-96c5-bc80ae078a8c"},
    {"id": 461, "name": "Storii", "notion_page_id": "1d229bcc-b6fc-81be-a2f5-d67bf8b3af98"},
    {"id": 462, "name": "Strawberry Fields High School", "notion_page_id": "32629bcc-b6fc-818c-bae3-eb1d6a20bd9c"},
    {"id": 463, "name": "Stride Ventures", "notion_page_id": "10529bcc-b6fc-8055-b885-dd273e461871"},
    {"id": 464, "name": "Supercharge.vc", "notion_page_id": "23029bcc-b6fc-80d2-95a0-c2fcf4245c96"},
    {"id": 465, "name": "Supernova", "notion_page_id": "12329bcc-b6fc-80e5-90d4-ea2f81da28c0"},
    {"id": 466, "name": "SupportEngineer AI", "notion_page_id": "11529bcc-b6fc-8039-8cf7-d582124f119d"},
    {"id": 467, "name": "SuprSend", "notion_page_id": "85d03842-bdaa-4ac4-8ad6-a9c52f7c94e9"},
    {"id": 468, "name": "Sutter Hill Ventures", "notion_page_id": "32629bcc-b6fc-8139-9c45-dc735527e922"},
    {"id": 469, "name": "Switchyards", "notion_page_id": "ee336bba-f5ff-4602-860f-8ce28ccc3233"},
    {"id": 470, "name": "Taakat", "notion_page_id": "12adf0bf-2bf1-4523-a9e9-ee78916008e0"},
    {"id": 471, "name": "Takshil Venture Partners", "notion_page_id": "29b29bcc-b6fc-80e5-83c2-f1b403f3b6b4"},
    {"id": 472, "name": "TapDrop", "notion_page_id": "15129bcc-b6fc-80dc-b9fb-f8bfe1433e63"},
    {"id": 473, "name": "TE Connectivity", "notion_page_id": "32629bcc-b6fc-8167-848a-e5a1a75187b1"},
    {"id": 474, "name": "Tenacio", "notion_page_id": "12029bcc-b6fc-80a7-8afd-d24206c99986"},
    {"id": 475, "name": "Tensol", "notion_page_id": "32629bcc-b6fc-8132-95b7-d958b4e7273e"},
    {"id": 476, "name": "Terafac", "notion_page_id": "13629bcc-b6fc-801d-b2b2-cd64e8d21d3d"},
    {"id": 477, "name": "Terra.do", "notion_page_id": "7f0162b4-1f0f-4501-9ea9-dcd1d0d3f56e"},
    {"id": 478, "name": "Terractive", "notion_page_id": "a1aeaea4-866b-4703-b35d-2b7723ce3120"},
    {"id": 479, "name": "Tesora AI", "notion_page_id": "22c29bcc-b6fc-81de-a071-d4cdfe2f9268"},
    {"id": 480, "name": "Tessary", "notion_page_id": "32729bcc-b6fc-8182-97c8-fb51ca8a4a4b"},
    {"id": 481, "name": "Tessera Labs", "notion_page_id": "32629bcc-b6fc-818a-8247-d593d1284262"},
    {"id": 482, "name": "Texinno", "notion_page_id": "1e429bcc-b6fc-800b-80cc-c6f8a4678970"},
    {"id": 483, "name": "Thariq's new company", "notion_page_id": "22d29bcc-b6fc-80bf-96e0-de4ce8f22c50"},
    {"id": 484, "name": "The Faculty of Engineering at Lund University", "notion_page_id": "32629bcc-b6fc-8157-b930-f161b13f2057"},
    {"id": 485, "name": "The Medical Travel Company", "notion_page_id": "10b29bcc-b6fc-8091-aab2-da2be29d272b"},
    {"id": 486, "name": "The Shovel Company", "notion_page_id": "1ed29bcc-b6fc-80df-996d-c3eb3bf33445"},
    {"id": 487, "name": "The University of North Carolina at Chapel Hill", "notion_page_id": "32629bcc-b6fc-816a-a296-c11e3f6ac60e"},
    {"id": 488, "name": "TheFounderVC", "notion_page_id": "24e29bcc-b6fc-8097-8cfe-d3947eee12b4"},
    {"id": 489, "name": "Together Fund", "notion_page_id": "b5640522-01f6-4155-b27c-c33d0de2ade7"},
    {"id": 595, "name": "Tonic Music", "notion_page_id": "006db77c-686c-400a-9b62-f8a81390a2f8"},
    {"id": 490, "name": "Tower Research Capital", "notion_page_id": "22529bcc-b6fc-812c-9a55-d57c751fae95"},
    {"id": 491, "name": "Trackk", "notion_page_id": "29b29bcc-b6fc-81f9-a078-c07925d2762f"},
    {"id": 492, "name": "Tractor Factory", "notion_page_id": "031d8fb5-c588-416d-a527-ad9f3553ced1"},
    {"id": 493, "name": "Tradeface", "notion_page_id": "24629bcc-b6fc-80b8-adcd-ccd3c1738c82"},
    {"id": 494, "name": "TruFides AI", "notion_page_id": "1f529bcc-b6fc-8032-9069-e327e428b199"},
    {"id": 495, "name": "Truva Homes", "notion_page_id": "0f844fee-d44b-4a4b-969d-86d638bc108e"},
    {"id": 496, "name": "Turnover", "notion_page_id": "419e04ca-f855-4bec-9579-b37b341780c3"},
    {"id": 497, "name": "Tykhe Block Ventures", "notion_page_id": "fc45f9dc-ebf2-4a54-bcb0-f2bf6afccd7e"},
    {"id": 498, "name": "UC Berkeley Management, Entrepreneurship, & Technology (M.E.T.) program", "notion_page_id": "32629bcc-b6fc-816a-85e6-c5edf7608c9b"},
    {"id": 499, "name": "UGX AI", "notion_page_id": "18a29bcc-b6fc-807e-a870-c46cf648b6cd"},
    {"id": 594, "name": "Ukhi", "notion_page_id": "0058eac2-aa91-4bf7-ad49-cd10c1e55149"},
    {"id": 500, "name": "Uncorrelated VC", "notion_page_id": "25029bcc-b6fc-8078-b341-d63946e97de7"},
    {"id": 501, "name": "UnderNeat", "notion_page_id": "15029bcc-b6fc-809c-8335-d80dd3ba2c51"},
    {"id": 502, "name": "Unusual VC", "notion_page_id": "30d29bcc-b6fc-80f3-a4b8-d3c8070221a6"},
    {"id": 503, "name": "Up & Run", "notion_page_id": "1e229bcc-b6fc-80ed-ba69-cf13c4829540"},
    {"id": 504, "name": "Uravu Labs", "notion_page_id": "7e00b851-672d-4ad3-9644-eb216d8f1ba3"},
    {"id": 505, "name": "Vaibhav Jain's company", "notion_page_id": "22a29bcc-b6fc-818e-9371-ef1f0b149d61"},
    {"id": 506, "name": "Vantara AI", "notion_page_id": "22d29bcc-b6fc-8098-b46d-c7274c2896d8"},
    {"id": 507, "name": "Venture Catalyst", "notion_page_id": "b404069f-54ac-42ea-bc73-74a4ce8ea103"},
    {"id": 508, "name": "Virtually", "notion_page_id": "020a0a37-dbed-49a4-b30a-ae422305972f"},
    {"id": 509, "name": "Vista Del Lago High School", "notion_page_id": "32629bcc-b6fc-81ee-8d8d-c00a4e085dee"},
    {"id": 510, "name": "Vitruv Motors", "notion_page_id": "17c29bcc-b6fc-80f1-bf65-ee178b022146"},
    {"id": 511, "name": "VoiceBit", "notion_page_id": "2e329bcc-b6fc-8120-aa05-f9e47250c2b4"},
    {"id": 512, "name": "Volt VC", "notion_page_id": "a375c52f-9574-43b2-9eaa-c49bdf408b7c"},
    {"id": 513, "name": "Volt14 Solutions", "notion_page_id": "1ea29bcc-b6fc-8047-874b-ee87e2988cb0"},
    {"id": 514, "name": "Weaver", "notion_page_id": "11429bcc-b6fc-807b-9bfc-c9b232f9ce8f"},
    {"id": 515, "name": "Weka", "notion_page_id": "14e29bcc-b6fc-8081-b91e-de81dfe0b08e"},
    {"id": 516, "name": "White Ventures", "notion_page_id": "168f84ee-b7dd-4837-8e72-cd8405062dcb"},
    {"id": 517, "name": "Whop", "notion_page_id": "32629bcc-b6fc-8176-a665-c35efbd8c8c2"},
    {"id": 518, "name": "Wing VC", "notion_page_id": "2a729bcc-b6fc-8089-ac74-ecd5f8c583b5"},
    {"id": 519, "name": "Wingy", "notion_page_id": "31029bcc-b6fc-81db-a600-cb4f06bf9f94"},
    {"id": 520, "name": "Wisely", "notion_page_id": "23a29bcc-b6fc-80c4-94f2-e372059aeefc"},
    {"id": 521, "name": "Wizly", "notion_page_id": "22629bcc-b6fc-8040-a4c1-df33c2289400"},
    {"id": 522, "name": "World Science University", "notion_page_id": "32629bcc-b6fc-814c-8175-e53fdc8b75f0"},
    {"id": 523, "name": "Xavier College Preparatory High School", "notion_page_id": "32629bcc-b6fc-81db-a08e-d7dacf43b5c1"},
    {"id": 524, "name": "Xavier School", "notion_page_id": "32629bcc-b6fc-8192-866e-d7864301ecc6"},
    {"id": 525, "name": "Xenova Dynamics", "notion_page_id": "31229bcc-b6fc-8125-87ae-dd40aff5e1af"},
    {"id": 526, "name": "Xook.ai", "notion_page_id": "410d68cd-cbe5-4726-9472-2835a1656666"},
    {"id": 527, "name": "xPay", "notion_page_id": "1ca29bcc-b6fc-803f-9086-e1aacb011b16"},
    {"id": 528, "name": "Yaary", "notion_page_id": "05f4fc55-2dda-4218-8728-b7134ec39534"},
    {"id": 529, "name": "Yadavindra Public School, Mohali", "notion_page_id": "32629bcc-b6fc-815c-a0e4-fe8aff2345b8"},
    {"id": 530, "name": "Yali Capital", "notion_page_id": "7ba6a221-9e09-447a-9a9e-cc82df0e6f29"},
    {"id": 605, "name": "YOYO AI (fka Trimpixel)", "notion_page_id": "328be182-566f-43b8-9461-7c9619fbf4f7"},
    {"id": 531, "name": "Z47 (f.k.a. Matrix Partners India)", "notion_page_id": "2cc54ffc-2206-4e54-be43-dc032e2c4a3c"},
    {"id": 532, "name": "Z5 Capital", "notion_page_id": "22429bcc-b6fc-8044-806a-eacf641bdeb9"},
    {"id": 533, "name": "Zapcover", "notion_page_id": "1d629bcc-b6fc-8074-a060-d18910b9033e"},
    {"id": 534, "name": "Zetta Venture Partners", "notion_page_id": "27b29bcc-b6fc-802e-ba11-c9eec7d94d9b"},
    {"id": 535, "name": "ZFunds", "notion_page_id": "27829bcc-b6fc-807b-ad4d-ee0d710c9898"},
    {"id": 536, "name": "Ziffi Chess", "notion_page_id": "2e3c2b90-dcb9-4789-8dd3-05250038e3e5"},
    {"id": 537, "name": "Ziffy", "notion_page_id": "2b629bcc-b6fc-8056-a6a5-e3d005a84137"},
    {"id": 538, "name": "Zingroll", "notion_page_id": "1eb29bcc-b6fc-80fc-8fdc-e750dbef988d"},
    {"id": 539, "name": "Zivy (fka Zoven)", "notion_page_id": "30329bcc-b6fc-817b-8412-cd96c6ee2d52"},
    {"id": 540, "name": "Zoddle", "notion_page_id": "31029bcc-b6fc-80e1-a6c2-d051c5033963"},
    {"id": 541, "name": "ZoMint", "notion_page_id": "31129bcc-b6fc-8190-ad82-dc17d4938233"},
    {"id": 542, "name": "ZuAI", "notion_page_id": "17529bcc-b6fc-806b-a364-c1f68f7e1e42"},
]


def slugify(name: str) -> str:
    """Convert company name to a filesystem-safe slug."""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def extract_rich_text(rich_text_list: list) -> str:
    """Extract plain text from Notion rich_text array, preserving annotations."""
    parts = []
    for rt in rich_text_list:
        text = rt.get("plain_text", "")
        annotations = rt.get("annotations", {})
        href = rt.get("href")

        if annotations.get("code"):
            text = f"`{text}`"
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        if href:
            text = f"[{text}]({href})"

        parts.append(text)
    return "".join(parts)


def block_to_markdown(block: dict, indent: int = 0) -> str:
    """Convert a single Notion block to markdown."""
    block_type = block.get("type", "")
    prefix = "  " * indent

    if block_type == "paragraph":
        text = extract_rich_text(block["paragraph"].get("rich_text", []))
        return f"{prefix}{text}\n" if text else "\n"

    elif block_type.startswith("heading_"):
        level = int(block_type[-1])
        text = extract_rich_text(block[block_type].get("rich_text", []))
        return f"{prefix}{'#' * level} {text}\n"

    elif block_type == "bulleted_list_item":
        text = extract_rich_text(block["bulleted_list_item"].get("rich_text", []))
        return f"{prefix}- {text}\n"

    elif block_type == "numbered_list_item":
        text = extract_rich_text(block["numbered_list_item"].get("rich_text", []))
        return f"{prefix}1. {text}\n"

    elif block_type == "to_do":
        checked = block["to_do"].get("checked", False)
        text = extract_rich_text(block["to_do"].get("rich_text", []))
        checkbox = "[x]" if checked else "[ ]"
        return f"{prefix}- {checkbox} {text}\n"

    elif block_type == "toggle":
        text = extract_rich_text(block["toggle"].get("rich_text", []))
        return f"{prefix}<details><summary>{text}</summary>\n"

    elif block_type == "code":
        text = extract_rich_text(block["code"].get("rich_text", []))
        lang = block["code"].get("language", "")
        return f"{prefix}```{lang}\n{text}\n```\n"

    elif block_type == "quote":
        text = extract_rich_text(block["quote"].get("rich_text", []))
        return f"{prefix}> {text}\n"

    elif block_type == "callout":
        icon = block["callout"].get("icon", {})
        emoji = icon.get("emoji", "") if icon else ""
        text = extract_rich_text(block["callout"].get("rich_text", []))
        return f"{prefix}> {emoji} {text}\n"

    elif block_type == "divider":
        return f"{prefix}---\n"

    elif block_type == "table_of_contents":
        return ""

    elif block_type == "bookmark":
        url = block["bookmark"].get("url", "")
        caption = extract_rich_text(block["bookmark"].get("caption", []))
        return f"{prefix}[{caption or url}]({url})\n"

    elif block_type == "image":
        img = block["image"]
        url = ""
        if img.get("type") == "external":
            url = img["external"].get("url", "")
        elif img.get("type") == "file":
            url = img["file"].get("url", "")
        caption = extract_rich_text(img.get("caption", []))
        return f"{prefix}![{caption}]({url})\n"

    elif block_type == "embed":
        url = block["embed"].get("url", "")
        return f"{prefix}[Embed: {url}]({url})\n"

    elif block_type == "link_preview":
        url = block["link_preview"].get("url", "")
        return f"{prefix}[Link: {url}]({url})\n"

    elif block_type == "table":
        return ""  # Table rows handled separately

    elif block_type == "table_row":
        cells = block["table_row"].get("cells", [])
        row = " | ".join(extract_rich_text(cell) for cell in cells)
        return f"{prefix}| {row} |\n"

    elif block_type == "column_list":
        return ""

    elif block_type == "column":
        return ""

    elif block_type == "child_page":
        title = block["child_page"].get("title", "")
        return f"{prefix}[Child Page: {title}]\n"

    elif block_type == "child_database":
        title = block["child_database"].get("title", "")
        return f"{prefix}[Child Database: {title}]\n"

    elif block_type == "synced_block":
        return ""  # Children will be fetched recursively

    elif block_type == "link_to_page":
        return f"{prefix}[Link to page]\n"

    else:
        return f"{prefix}<!-- {block_type} block -->\n"


def fetch_blocks(page_id: str) -> list:
    """Fetch all blocks for a page, handling pagination."""
    all_blocks = []
    url = f"{BASE_URL}/blocks/{page_id}/children"
    params = {"page_size": 100}

    while True:
        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", 1))
            print(f"    Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            continue
        if resp.status_code != 200:
            print(f"    Error {resp.status_code}: {resp.text[:200]}")
            return all_blocks

        data = resp.json()
        all_blocks.extend(data.get("results", []))

        if not data.get("has_more"):
            break
        params["start_cursor"] = data["next_cursor"]
        time.sleep(0.35)

    return all_blocks


def fetch_children_recursive(block_id: str, depth: int = 0, max_depth: int = 3) -> str:
    """Recursively fetch child blocks and convert to markdown."""
    if depth >= max_depth:
        return ""

    blocks = fetch_blocks(block_id)
    md_parts = []
    is_table = False
    table_header_done = False

    for block in blocks:
        block_type = block.get("type", "")

        if block_type == "table":
            is_table = True
            table_header_done = False
            # Fetch table rows
            if block.get("has_children"):
                time.sleep(0.35)
                child_blocks = fetch_blocks(block["id"])
                for i, child in enumerate(child_blocks):
                    row_md = block_to_markdown(child, indent=depth)
                    md_parts.append(row_md)
                    if i == 0 and not table_header_done:
                        # Add separator after header
                        cells = child.get("table_row", {}).get("cells", [])
                        sep = " | ".join("---" for _ in cells)
                        md_parts.append(f"| {sep} |\n")
                        table_header_done = True
            is_table = False
            continue

        md = block_to_markdown(block, indent=depth)
        md_parts.append(md)

        # Recursively fetch children
        if block.get("has_children") and block_type not in ("table", "child_page", "child_database"):
            time.sleep(0.35)
            child_md = fetch_children_recursive(block["id"], depth + 1, max_depth)
            if child_md:
                md_parts.append(child_md)

    return "".join(md_parts)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total = len(COMPANIES)
    fetched = 0
    skipped = 0
    errors = 0
    empty = 0

    for i, company in enumerate(COMPANIES):
        name = company["name"]
        page_id = company["notion_page_id"]
        slug = slugify(name)
        filepath = os.path.join(OUTPUT_DIR, f"{slug}.md")

        # Skip if existing file > 500 bytes
        if os.path.exists(filepath) and os.path.getsize(filepath) > 500:
            print(f"[{i+1}/{total}] SKIP (exists > 500B): {name}")
            skipped += 1
            continue

        print(f"[{i+1}/{total}] Fetching: {name} ({page_id})")

        try:
            md_content = fetch_children_recursive(page_id)

            if not md_content.strip():
                # Write a minimal placeholder
                md_content = f"# {name}\n\n*No page body content found.*\n"
                empty += 1

            # Add frontmatter
            full_content = f"# {name}\n\n{md_content}"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full_content)

            size = os.path.getsize(filepath)
            print(f"    Saved: {slug}.md ({size} bytes)")
            fetched += 1

        except Exception as e:
            print(f"    ERROR: {e}")
            errors += 1

        time.sleep(0.35)

    print(f"\n{'='*60}")
    print(f"DONE: {fetched} fetched, {skipped} skipped, {empty} empty, {errors} errors")
    print(f"Total companies: {total}")


if __name__ == "__main__":
    main()
