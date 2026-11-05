# Socket-Application
Đồ án xây dụng một ứng dụng nhắn tin trong mạng WLAN

## Cách chạy code:
### Các cờ:
- --name: Đặt tên người dùng
- --tcp-port: Xác định cổng cho giao thức TCP (mặc định 5050)
- --bcast: Chọn kênh để broadcast (mặc định 255.255.255.255, có thể thay 127.255.255.255 nếu không có kết nối wifi)
### Ví dụ câu lệnh khởi chạy:
- VD: python .\src\main.py --name Matthew --tcp-port 6001
## Các tính năng:
- /help : Hiện các lệnh có thể dùng trong chương trình 
- /quit : Thoát khỏi chương trình
- /list : Hiển thị danh sách các người dùng khác trong mạng LAN và trạng thái online
- /status <online|away> : Chỉnh trạng thái hoạt động của bản thân thành online hoặc away
- /chat \<name\> : Kết nối và gửi tin nhắn tới người khác trong mạng
- \<any text\> : Gửi tin nhắn đến người đang kết nối
- /leave : Thoát khỏi cuộc trò chuyện hiện tại
