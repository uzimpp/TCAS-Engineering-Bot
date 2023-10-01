# Importing
import random
import json
import base64
import hashlib
import hmac
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage ,StickerMessage, StickerSendMessage , QuickReply, QuickReplyButton, MessageAction, AudioMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re


# Line Bot Config
line_bot_api = LineBotApi('*Channel access token*') #Channel access token
handler = WebhookHandler('*Channel secret*') #Channel secret

# Google Sheet Config
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

# Variables Config

# stage -1 = denied , waiting for a confirmation
# stage 0 = idle
# stage 1 = check_major
# stage 2 = processing check_major
# stage 3 = check_curriculum
# stage 4 = processing check_curriculum
# stage 5 = check_req
# stage 6 = processing check_req
# stage 7 = check_round , processing check_round

#image_url_full = 'https://i.imgur.com/MoMWaTJ.png'
#image_url_guide1 = 'https://i.imgur.com/e6lCWxn.png'
#image_url_guide2 = 'https://i.imgur.com/iWsILuw.png'
#image_url_uni = 'https://i.imgur.com/lWDrwqh.png'

images = [
    ImageSendMessage(original_content_url='https://i.imgur.com/e6lCWxn.png', preview_image_url='https://i.imgur.com/e6lCWxn.png'), #image_url_guide1
    ImageSendMessage(original_content_url='https://i.imgur.com/iWsILuw.png', preview_image_url='https://i.imgur.com/iWsILuw.png'), #image_url_guide2
    ImageSendMessage(original_content_url='https://i.imgur.com/lWDrwqh.png', preview_image_url='https://i.imgur.com/lWDrwqh.png') #image_url_uni
]
reporting_form = "https://forms.gle/Vz1sL4wDMF4znxBa9"

university = ['CU', 'KSU', 'KU', 'KBU', 'KKU', 'CMU', 'TSU', 'KMUTT', 'KMUTNB1', 'KMUTNB2', 'MUT', 'RMUTK', 'RMUTTO1', 'RMUTTO2',
              'RMUTT', 'RMUTP', 'RMUTR', 'RMUTL', 'RMUTSV1', 'RMUTSV2', 'RMUTI', 'SUT', 'TU', 'DPU', 'NPU', 'PNU', 'NU', 'BUU',
              'UP', 'MSU', 'MU', 'MJU', 'RSU', 'RTU', 'CPRU', 'BRSU', 'RU', 'WU', 'SWU', 'SPU', 'SU', 'PSU', 'SU(SiamU)', 'UTCC', 'UBU', 'KMITL']
activated = False
user_confirm = False
stage = 0
selected_uni = ''
worksheet = ''
data = []
major_list = []
selected_major = ''
curriculum_list = []
selected_curriculum = ''
req_list = []
req_list_row = []
selected_round = ''
skipped = 0
user_errors = 0
input_value = 0


# Lambda Config
def lambda_handler(event, context):
    signature = event['headers']['x-line-signature']
    body = event['body']
    hash = hmac.new('<CHANNEL_SECRET>'.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash).decode('utf-8')
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return {'statusCode': 400, 'body': 'Invalid signature.'}
    return {'statusCode': 200, 'body': 'OK'}


# Handle messages and sort type of the message
@handler.add(MessageEvent, message=(TextMessage, ImageMessage, StickerMessage))
def handle_message(event):
    global user_errors, stage, activated, user_confirm, skipped, selected_uni, worksheet, data, major_list, selected_major, curriculum_list, selected_curriculum, req_list, req_list_row, selected_round, input_value
    ########################################################################################################################################################
    if isinstance(event.message, TextMessage):
        ############################################################################
        # guide | วิธีการใช้งาน //
        if event.message.text == 'วิธีการใช้งาน':  ###########
            print("guide")
            line_bot_api.push_message(event.source.user_id, images)

        ############################################################################
        # website | เว็บไซต์ //
        elif event.message.text == 'เว็บไซต์':  ###########
            print("website")
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage("คุณสามารถศึกษาเพิ่มเติมได้ที่นี่ https://www.mytcas.com/"))   
        
        ############################################################################
        # reporting | รายงานปัญหา //
        elif event.message.text == ('รายงานปัญหา' or 'ข้อเสนอแนะ' or 'รายงานปัญหาและข้อเสนอแนะ'):  ###########
            print("reporting")
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(reporting_form))
        
        ############################################################################
        # the other | อื่นๆ //
        elif event.message.text == 'อื่นๆ':  ###########
            print("other")
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage("คุณสามารถศึกษาเว็บไซต์อื่นๆที่มีประโยชน์เพิ่มเติมได้ที่นี่ https://tcas.in.th/search/category?type=facGroup"))
        
        ############################################################################
        # activated Chatbot | เริ่มต้นการใช้งาน
        elif event.message.text == 'เริ่มต้นการใช้งาน':  ###########
            event.message.text = ""
            activated = True
            user_confirm = False
            stage = 0
            selected_uni = ''
            worksheet = ''
            data = []
            major_list = []
            selected_major = ''
            curriculum_list = []
            selected_curriculum = ''
            req_list = []
            req_list_row = []
            selected_round = ''
            skipped = 0
            user_errors = 0
            input_value = 0
            
            reset_variables()
            print("activated Chatbot")            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    'คุณต้องการทราบข้อมูลของ TCAS คณะวิศวกรรมศาสตร์ใช่หรือไม่\nถ้าใช่โปรดกดปุ่ม "ยืนยัน" ถ้าไม่ใช่โปรดกดปุ่ม "ปฏิเสธ"',
                    quick_reply=QuickReply(items=[QuickReplyButton(action=MessageAction(label="ยืนยัน", text="ยืนยัน")),
                                                  QuickReplyButton(action=MessageAction(label="ปฏิเสธ", text="ปฏิเสธ"))])))
                
        ######################################
        # accept and deny | ยืนยันและปฏิเสธ
        elif (event.message.text == "ยืนยัน" and activated) :
            event.message.text = ""
            user_confirm = True
            stage = 0

            reset_variables()
            print("accepted")            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    "กรุณาพิมพ์มหาวิทยาลัยที่คุณต้องการทราบข้อมูล"))
            line_bot_api.push_message(
                event.source.user_id, images[1])
            line_bot_api.push_message(
                event.source.user_id, images[2])
            

        elif (event.message.text == "ปฏิเสธ" or event.message.text == "ไม่ต้องการ") and (activated or stage == 4):
            event.message.text = ""
            user_confirm = False
            stage = -1
            
            reset_variables()
            
            print("denied")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    "หากคุณต้องการทราบข้อมูลคุณสามารถกดเมนูเริ่มต้นการใช้งานได้เลย"))
        
        ######################################
        # user warning | เตือนผู้ใช้งานเมื่อมีการพิมพ์ผิดอย่างต่อเนื่องทุกๆ 5 ครั้ง
        else:
            if not(activated and user_confirm) and stage <= 0:
                user_errors += 1
                print('user_errors',user_errors)
            pass
            
        if (user_errors % 5) == 0 and user_errors != 0: # Send a warning message and reset the error count
            user_errors = 0
            print('user_errors = warning')
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    'หากคุณต้องการความช่วยเหลือสามารถกดเมนูวิธีการใช้งานหรือกดปุ่ม"วิธีการใช้งาน"ได้ด้านล่าง',
                        quick_reply=QuickReply(items=[
                            QuickReplyButton(action=MessageAction(
                                label="วิธีการใช้งาน", text="วิธีการใช้งาน")),
                            QuickReplyButton(action=MessageAction(
                                label="ไม่ต้องการ", text="ไม่ต้องการ"))])))

        ######################################
        # check major | ตรวจสอบสาขาที่มีอยู่
        if (event.message.text.upper() in university and user_confirm and stage == 0) or (event.message.text == "สาขา" and stage == 7):
            if event.message.text != "สาขา" :
                selected_uni = event.message.text.upper()
            user_confirm = False
            input_value = 0
            user_errors = 0
            stage = 1
            check_major(event)

        elif ((event.message.text not in university) and (stage == 0 and user_confirm) and (stage not in range(1,8))):
            print("check major = error")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    "ขออภัย ไม่พบมหาวิทยาลัยที่คุณต้องการกรุณาพิมพ์มหาวิทยาลัยที่คุณต้องการทราบข้อมูลของคณะวิศวกรรมศาสตร์ใหม่อีกครั้ง"))
        
        ######################################
        # checking if message is int or not | ตรวจสอบข้อความว่าเป็นตัวเลขหรือไม่ เนื่องจาก event.message.text ที่เข้ามาเป็น str ในตอนแรกจคงต้องมีการเชคก่อนเปลี่ยนแปลงค่าไม่งั้นจะเกิด error
        try:
            input_value = int(event.message.text)
        except ValueError:
            pass

        ######################################
        # check curriculum | ตรวจสอบหลักสูตรที่มีอยู่
        if ((event.message.text.isdigit() and 1 <= input_value <= len(major_list)) and stage == 2 and skipped != 1) or (event.message.text == "หลักสูตร" and stage == 7):
            if event.message.text != "หลักสูตร" :
                selected_major = major_list[int(event.message.text)-1]
            input_value = 0
            user_errors = 0
            stage = 3
            check_curriculum(event)
        
        
        elif not(1 <= input_value <= len(major_list)) and stage == 2 and stage != 7 and skipped != 1 and len(major_list) > 1:
            print("check curriculum = error")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    "ขออภัย กรุณาเลือกสาขาที่คุณสนใจ\nด้วยการพิมพ์ตัวเลข 1 - " + str(len(major_list)) + "โดยไม่ต้องมีจุด"))
        
        ######################################
        # check req | ตรวจสอบเกณฑ์ในการรับสมัคร
        elif ((1 <= input_value <= len(curriculum_list)) and stage == 4 and skipped != 1) or (event.message.text == "รอบ" and stage == 7):
            if event.message.text != "รอบ" :    
                selected_curriculum = curriculum_list[int(event.message.text)-1]
            input_value = 0
            user_errors = 0
            stage = 5
            check_req(event)


        elif not(1 <= input_value <= len(curriculum_list)) and stage == 4 and skipped != 1 and len(curriculum_list) > 1:
            print("check req = error")
            line_bot_api.push_message(
            event.source.user_id, TextSendMessage(
                "ขออภัย กรุณาเลือกหลักสูตรข้างล่างนี้ด้วยการกดปุ่ม Quick reply\n" +
                '\n'.join(curriculum_list),
                quick_reply=QuickReply(items=[QuickReplyButton(action=MessageAction(
                    label="หลักสูตรที่ "+ str(e+1), text=e+1)) for e in range(len(curriculum_list))])))
        
        ######################################
        # check round | ตรวจสอบรอบ
        elif (event.message.text.isdigit() and 1 <= input_value <= 4) and stage == 6:
            selected_round = req_list[int(event.message.text)-1]
            input_value = 0
            user_errors = 0
            stage = 7
            check_round(event)

        elif not(1 <= input_value <= 4) and stage == 6 and skipped != 1 and len(req_list) > 1:
            print("check round = error")
            line_bot_api.push_message(
            event.source.user_id,
            TextSendMessage("ขออภัย กรุณาเลือกเกณฑ์การรับสมัครในรอบที่คุณสนใจด้วยการกดปุ่ม Quick reply",
                            quick_reply=QuickReply(items=[QuickReplyButton(action=MessageAction(
                                label="รอบ 1", text="1")),
                                QuickReplyButton(action=MessageAction(
                                    label="รอบ 2", text="2")),
                                QuickReplyButton(action=MessageAction(
                                    label="รอบ 3", text="3")),
                                QuickReplyButton(action=MessageAction(
                                    label="รอบ 4", text="4"))])))
                    
    ########################################################################################################################################################
    # reply stickers from users | ตอบกลับ sticker จาก user
    elif isinstance(event.message, StickerMessage):
        send_stickers(event)
        
    ########################################################################################################################################################
    # reply images from user | ตอบกลับรูปภาพจาก user
    elif isinstance(event.message, ImageMessage):
        print("reply with ty for img")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage("ขอบคุณสำหรับไฟล์รูปภาพ <3\nหากคุณต้องการเริ่มต้นใช้งานให้คุณกดเมนูเริ่มต้นการใช้งานได้เลย"))
    
    ########################################################################################################################################################


def check_major(event):
    global stage, activated, user_confirm, skipped, selected_uni, worksheet, data, major_list, selected_major, curriculum_list, selected_curriculum, req_list, req_list_row, selected_round
    input_value = 0
    skipped = 0
    worksheet = client.open('sn-all-engineer').worksheet(selected_uni)
    data = worksheet.get_all_values()
    major_list = [row[0] for row in data[1:] if row[0]]
    major_list = sorted(
        set(major_list), key=lambda x: int(x.split('.')[0]))  # เรียงลำดับตามเลขหน้าจากน้อยไปหามาก
    if len(major_list) == 1:
        messages = "จาก " + selected_uni + " มีเพียง " + major_list[0]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                messages))
        selected_major = major_list[0]
        stage = 3
        skipped = 1
        print("skipped to check_curriculum", selected_major)
        check_curriculum(event)
    else:
        stage = 2
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                "กรุณาเลือกสาขาจากข้างล่างนี้ด้วยการพิมพ์ต้วเลขด้านหน้าโดยไม่ต้องมีจุด\n" + "\n".join(major_list)))
    print("check_major",selected_uni,"\n", major_list)

def check_curriculum(event):
    global stage, activated, user_confirm, skipped, selected_uni, worksheet, data, major_list, selected_major, curriculum_list, selected_curriculum, req_list, req_list_row, selected_round
    input_value = 0
    skipped = 0
    # หา row ที่มี major นั้นๆเพื่อนำ row ดังกล่าวไปหาต่อใน column C แล้วเก็บ เป็น list ที่เป็น set เพื่อไม่ให้ซ้ำ
    curriculum_list_row = [i+1 for i,
                           row in enumerate(data) if row[0] == selected_major]
    curriculum_list = [data[row-1][2]
                       for row in curriculum_list_row if row <= len(data)]
    curriculum_list = sorted(set(curriculum_list),
                             key=lambda x: int(x.split('.')[0]))

    print(curriculum_list_row, curriculum_list)
    if len(curriculum_list) == 1:
        messages = "จาก " + selected_major + \
            " มีเพียง "+', '.join(curriculum_list)
        line_bot_api.push_message(
            event.source.user_id,
            TextSendMessage(
                messages))
        selected_curriculum = curriculum_list[0]
        stage = 5
        skipped = 1
        print("skipped to check_req", selected_curriculum)
        check_req(event)
    else:
        stage = 4
        line_bot_api.push_message(
            event.source.user_id, TextSendMessage(
                "กรุณาเลือกหลักสูตรข้างล่างนี้\n" +
                '\n'.join(curriculum_list),
                quick_reply=QuickReply(items=[QuickReplyButton(action=MessageAction(
                    label="หลักสูตรที่ "+str(i+1), text=i+1)) for i in range(len(curriculum_list))])))
    print("check_curriculum",selected_major,"\n",curriculum_list)

def check_req(event):
    global stage, activated, user_confirm, skipped, selected_uni, worksheet, data, major_list, selected_major, curriculum_list, selected_curriculum, req_list, req_list_row, selected_round
    input_value = 0
    skipped = 0
    req_list_row = [i+1 for i,
                    row in enumerate(data) if row[2] == selected_curriculum]
    req_list = [data[row - 1][4] for row in req_list_row]
    if len(req_list) == 6:
        req_str = req_list[5]
    else:
        req_str = req_list[0]

    req_list = re.split("(?=รอบ\d{1,4})", req_str)
    if req_list[0] == '':# delete '' from the list
        req_list = req_list[1:] # most of the time there is '' in the first value of the list which possibly causes errors
    req_list = [re.sub(r"(รอบ)(\d)", rf"รอบที่ \2 ", element.replace("\n", "คือ\nรอบ ", 1)) for element in req_list]
    print(req_list)
    if req_list == []:
        stage = 7
        if len(curriculum_list) == 1:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage("ขออภัย ไม่พบข้อมูลการเปิดรับสมัครในหลักสูตรดังกล่าว\nหากคุณต้องการทราบข้อมูลให้คุณเลือกข้อมูลที่ต้องการทราบใหม่ได้เลย",
                                quick_reply=QuickReply(items=[
                                    QuickReplyButton(action=MessageAction(
                                        label="สาขา", text="สาขา")),
                                    QuickReplyButton(action=MessageAction(
                                        label="ไม่ต้องการ", text="ไม่ต้องการ"))])))
        else:
            line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage("ขออภัย ไม่พบข้อมูลการเปิดรับสมัครในหลักสูตรดังกล่าว\nหากคุณต้องการทราบข้อมูลให้คุณเลือกข้อมูลที่ต้องการทราบใหม่ได้เลย",
                                quick_reply=QuickReply(items=[
                                    QuickReplyButton(action=MessageAction(
                                        label="สาขา", text="สาขา")),
                                    QuickReplyButton(action=MessageAction(
                                        label="หลักสูตร", text="หลักสูตร")),
                                    QuickReplyButton(action=MessageAction(
                                        label="ไม่ต้องการ", text="ไม่ต้องการ"))])))
        print("no req is found , let the user choose again")
    else:
        stage = 6
        line_bot_api.push_message(
            event.source.user_id,
            TextSendMessage('คุณต้องการทราบข้อมูลในรอบใด?',
                            quick_reply=QuickReply(items=[QuickReplyButton(action=MessageAction(
                                label="รอบ 1", text="1")),
                                QuickReplyButton(action=MessageAction(
                                    label="รอบ 2", text="2")),
                                QuickReplyButton(action=MessageAction(
                                    label="รอบ 3", text="3")),
                                QuickReplyButton(action=MessageAction(
                                    label="รอบ 4", text="4"))])))
    print("check_req", selected_curriculum,"\n",req_list)

def check_round(event):
    global stage, activated, user_confirm, skipped, selected_uni, worksheet, data, major_list, selected_major, curriculum_list, selected_curriculum, req_list, req_list_row, selected_round
    input_value = 0
    stage = 7
    req_url = set([data[row - 1][3] for row in req_list_row])
    req_url = next(iter(req_url))
    print("check round" ,selected_round, req_url)
    messages = selected_round + "\n" + \
                "ศึกษาเพิ่มเติมได้ที่นี่" + "\n" + req_url
    line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(messages))
    line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage("คุณต้องการทราบข้อมูลส่วนใดใหม่หรือไม่?",
                                quick_reply=QuickReply(items=[
                                    QuickReplyButton(action=MessageAction(
                                        label="สาขา", text="สาขา")),
                                    QuickReplyButton(action=MessageAction(
                                        label="หลักสูตร", text="หลักสูตร")),
                                    QuickReplyButton(action=MessageAction(
                                        label="รอบ", text="รอบ")),
                                    QuickReplyButton(action=MessageAction(
                                        label="ไม่ต้องการ", text="ไม่ต้องการ"))])))


def send_stickers(event):
    sticker_list = [
            {
                "package_id": "789",
                "sticker_id": "10877"
            },
            {
                "package_id": "789",
                "sticker_id": "10882"
            },
            {
                "package_id": "446",
                "sticker_id": "1993"
            },
            {
                "package_id": "1070",
                "sticker_id": "17866"
            }]
    random_sticker = random.choice(sticker_list)
    # send sticker randomly | ส่งสติกเกอร์แบบแรนดอม
    print("reply with a sticker")
    line_bot_api.reply_message(event.reply_token, StickerSendMessage(
            package_id=random_sticker['package_id'], sticker_id=random_sticker['sticker_id']))


def reset_variables():
    global selected_uni, worksheet, data, major_list, selected_major, curriculum_list, selected_curriculum, req_list, req_list_row, selected_round, user_errors, stage, user_confirm, skipped, input_value
    selected_uni = ''
    worksheet = ''
    data = []
    major_list = []
    selected_major = ''
    curriculum_list = []
    selected_curriculum = ''
    req_list = []
    req_list_row = []
    selected_round = ''
    skipped = 0
    user_errors = 0
    input_value = 0
