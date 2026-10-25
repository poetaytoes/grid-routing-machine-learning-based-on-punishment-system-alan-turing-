# Nhóm 2 — Mô phỏng Learning Machine bằng thưởng và phạt

Bản mã nguồn tối thiểu để chạy demo Q-learning trong báo cáo và bài thuyết trình của nhóm. Agent học trên hai Grid World 5×5 và 8×8. Giao diện tiếng Việt hiển thị cập nhật Q-value, reward, số bước, tỷ lệ thành công và đường đi trước/sau học.

## Cài đặt và chạy

Cần Python 3.10 trở lên và trình duyệt web. Thư viện duy nhất cần cài là NumPy. Chạy các lệnh sau trong thư mục chứa README này:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m gridrl.course_server --port 8767
```

Mở **http://127.0.0.1:8767/**. Sau khi cài đặt, có thể nhấp đúp `start_demo.bat` trên Windows để khởi động lại. Giữ cửa sổ terminal mở trong lúc demo; nhấn `Ctrl+C` để dừng máy chủ. Nếu máy dùng lệnh `py` thay cho `python`, dùng `py -3 -m venv .venv` ở bước đầu.

Trên macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m gridrl.course_server --port 8767
```

Chỉ lần cài thư viện cần mạng. Sau đó demo chạy cục bộ, không cần tài khoản, API key, mô hình tải sẵn hay dịch vụ biểu đồ bên ngoài. Các liên kết tài liệu tham khảo trong giao diện cần mạng khi mở.

Nếu cổng 8767 đang được dùng, chạy với `--port 8768` rồi mở `http://127.0.0.1:8768/`.

## Kịch bản trình diễn

1. Chọn lưới 5×5, 500 episode, seed 42. Dùng reward đến đích +10, hành động sai −5, bước đi thông thường −1.
2. Tạo lại phiên học để bảng Q bắt đầu từ 0. Thực hiện từng bước và giải thích trạng thái, hành động, reward cùng giá trị Q trước/sau cập nhật.
3. Cho agent học tự động. Quan sát biểu đồ reward, lỗi, số bước và tỷ lệ đến đích. So sánh đường đi episode đầu với đường greedy sau học.
4. Tạo lại phiên với cùng seed và số episode, đổi phạt lỗi thành −10 để quan sát tác động. Đổi mức phạt cũng đổi thang điểm, vì vậy cần so sánh cả số lỗi, số bước và tỷ lệ thành công.
5. Thử lưới 8×8, sau đó chọn bản đồ bị chặn để xem `UNSOLVABLE`. Tải JSON từ giao diện nếu cần giữ kết quả phiên demo.

## Quy tắc và giới hạn

- Bốn hành động: Up, Right, Down, Left. Không đi chéo.
- Mỗi hành động nhận một loại reward: đến G +10; chạm vật cản/vượt biên −5 hoặc mức phạt đã chọn; bước hợp lệ còn lại −1. Phạt lỗi luôn ít nhất 5 điểm.
- Cập nhật: `Q(s,a) ← Q(s,a) + α [r + γ max Q(s',a') − Q(s,a)]`. Tại đích, phần giá trị tương lai bằng 0. Policy dùng epsilon-greedy trong khi học.
- `SOLVED`: policy tạo được đường hợp lệ tới G. `AGENT_FAILED`: policy chưa tìm được đường. `UNSOLVABLE`: kiểm tra reachability chính xác xác nhận không tồn tại đường.
- BFS chỉ kiểm tra khả năng đi tới đích và cung cấp độ dài tối ưu để đối chiếu. Demo không dùng đường BFS thay cho đường của policy.
- Q-learning dạng bảng học riêng từng bản đồ. Đây không phải LLM và không bảo đảm tổng quát hóa sang mê cung mới.
- Trạng thái học nằm trong bộ nhớ máy chủ. Dừng máy chủ làm mất phiên hiện tại nếu chưa tải JSON. Các tab trình duyệt cùng kết nối một máy chủ dùng chung phiên học.

## Các tệp cần thiết

| Tệp | Vai trò |
| --- | --- |
| `gridrl/__init__.py` | Khai báo package Python |
| `gridrl/course.py` | Reward, Q-learning, ghi nhận episode và đánh giá policy |
| `gridrl/environment.py` | Đọc Grid World, kiểm tra ô và BFS tham chiếu |
| `gridrl/course_server.py` | Máy chủ HTTP/API cục bộ |
| `course_dashboard/index.html` | Giao diện tiếng Việt |
| `course_dashboard/course.css` | Định dạng giao diện |
| `course_dashboard/course.js` | Điều khiển demo, biểu đồ và tải JSON |
| `requirements.txt` | Thư viện NumPy |
| `start_demo.bat` | Khởi động trên Windows sau khi cài đặt |
| `.gitignore` | Loại môi trường ảo và cache khỏi Git |

Phạm vi gói này là demo Q-learning chính trong bài thuyết trình. Nghiên cứu Double DQN bổ sung, dữ liệu thực nghiệm đã lưu, các tệp DOCX/PPTX và công cụ tạo báo cáo được lưu riêng.
