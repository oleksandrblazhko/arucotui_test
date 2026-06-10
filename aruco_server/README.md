Для такого сервера доцільно перейти від монолітної архітектури до архітектури з окремими відповідальностями (Separation of Concerns).

Зараз програма виконує одночасно:

Обробку аргументів командного рядка.
Завантаження калібрування камери.
Ініціалізацію камери.
Ініціалізацію ArUco-детектора.
Перетворення матриці обертання в кути Ейлера.
Виявлення маркерів.
Оцінку пози (Pose Estimation).
Формування OSC-повідомлень.
Передачу OSC-повідомлень.
Відображення відео.
Головний цикл.

Для подальшого розвитку (One Euro, Kalman, MQTT, WebSocket, запис логів) я б рекомендував:

aruco_server/
│
├── main.py
├── config.py
│
├── core/
│   ├── __init__.py
│   ├── calibration.py
│   ├── camera.py
│   ├── aruco_detector.py
│   ├── pose.py
│   └── marker.py
│
├── models/
│   ├── __init__.py
│   └── marker_data.py
│
├── filters/
│   ├── __init__.py
│   ├── base_filter.py
│   ├── ema_filter.py
│   ├── one_euro_filter.py
│   ├── marker_filter.py
│   └── marker_filter_manager.py
│
├── communication/
│   ├── __init__.py
│   └── osc_sender.py
│
├── ui/
│   ├── __init__.py
│   └── visualization.py
│
└── camera_ext.json