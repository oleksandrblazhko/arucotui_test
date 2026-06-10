# **ArUco-TUI Client v25.3**

**Author:** Rong-Hao Liang (TU Eindhoven)
**Email:** r.liang@tue.nl

This Processing sketch acts as a client for a Tangible User Interface (TUI) system based on ArUco marker tracking. It receives data from an external marker-detection script (e.g., Python with OpenCV) via OSC messages.

The system tracks individual ArUco tags, groups them into "Tagged Objects" (TOs), and maps their positions and orientations from 3D camera space to the 2D screen space. Users can interact with on-screen "Data Objects" (DOs) by moving and rotating the physical Tagged Objects over them.

## **Features**

* **OSC Client:** Listens on port 9000 for /marker messages containing tag ID, 3D position (tx, ty, tz), 3D rotation (rx, ry, rz), and corner points.  
* **Homography Calibration:** Uses a set of corner markers (IDs {1, 3, 2, 0} by default) from a calibration image (ArUco\_Grid15.png) to calculate a homography matrix. This maps the 3D tracking data to the 2D screen.  
* **Tag Management:** Manages the state (present, absent, updated) of all detected tags with a Time-To-Live (TTL) system.  
* **Tagged Object (TO) System:** Defines tangible objects as groups of one or more tags with specific offsets.  
* **Data Object (DO) Interaction:** Allows tangible objects (TOs) to "hit" and control on-screen Data Objects.  
* **Multiple Gesture Modes:** Supports different interaction modes, selectable via keyboard.  
* **Debug Views:** Provides multiple debug overlays to visualize tags, gestures, and data object states.

## **Setup**

1. **Run External Detection:** Start your external ArUco detection script (e.g., Python, OpenCV) that sends OSC messages to this client's IP address on port 9000\.  
2. **Prepare AruCo-markers**: 
   * Use one of generators (https://chev.me/arucogen/) 
   * Print on draw markers with the tag IDs
3. **Configure Sketch:** Open ArUcoTUI\_Client.pde and configure the following:  
   * TO\_IDs: Define the tag IDs that make up each tangible object.  
   * TO\_Offsets: Define the 3D offsets (in meters) for each tag within its tangible object.  
   * paperWidthOnScreen: Measure the real-world width (in mm) of your calibration sheet and update this value.  
   * markerWidth: The width (in mm) of your markers.  
   * touchThreshold: The distance (in meters) from the plane to consider a TO as "touching".  
4. **Run Processing Sketch:** Run the ArUcoTUI\_Client.pde file.  
5. **Calibrate:**  
   * The sketch will start in calibration mode, showing the calibration image.  
   * Prepare the calibration sheet with corner-markers (original ArUco-markers Id=1,3,2,0 clockwise from the top left corner) - client\ArUcoTUI_Client\data\ArUco_Grid15.png
   * Place the calibration sheet on the surface so it's visible to the camera.  
   * Once all corner markers are detected, the sketch will automatically calculate the homography and switch to interaction mode.  
   * Press the SPACE bar at any time to re-enter calibration mode.


### Детальний опис змінних

TO_IDs (Tagged Object IDs)

   1 int[][] TO_IDs = {{4}, {5}, {6}, {7}};

   * Призначення: Ця змінна визначає, які ArUco маркери належать до кожного фізичного об'єкта (Tagged Object). Це двовимірний масив цілих чисел. Кожен внутрішній масив {{...}} представляє один TaggedObject, а числа всередині — це унікальні ідентифікатори (ID) ArUco маркерів, які закріплені на цьому об'єкті.
   * Значення для системи: Ця змінна дозволяє системі згрупувати кілька маркерів як один логічний фізичний об'єкт, а також ідентифікувати різні об'єкти за їхніми маркерами.

TO_Offsets (Tagged Object Offsets)

* Призначення: Ця змінна задає зміщення (offset) для кожного маркера відносно центральної точки (pivot point) 
або точки захоплення відповідного TaggedObject. Це двовимірний масив об'єктів PVector, де кожен PVector містить зміщення по осях X, Y та Z у метрах.
Наведемо приклад для 6-гранного кубика розміром 30 мм, з 5 маркерами.
Початкові припущення та визначення:
   1. Розмір кубика: Сторона = 30 мм = 0.03 метра.
   2. Центр кубика: Для зручності ми будемо вважати, що центр фізичного кубика знаходиться в точці (0, 0, 0) його власної локальної системи координат.
   3. Осі:
       * Вісь X: Проходить через центр кубика, паралельно двом протилежним бічним граням.
       * Вісь Y: Проходить через центр кубика, паралельно іншим двом бічним граням.
       * Вісь Z: Проходить через центр кубика, вгору (від основи до верху).
   4. Позиція маркерів: Кожен маркер буде розташований точно в центрі відповідної грані.
   5. Відстань від центру до грані: Оскільки сторона кубика 30 мм, то від центру до будь-якої грані буде 30 мм / 2 = 15 мм = 0.015 метра.
  Визначення ID маркерів та їх положення:
  Використаємо такі ID для маркерів:
   * Маркер на верхній грані: ID 10
   * Маркер на "передній" бічній грані: ID 11 (припустимо, це грань, що дивиться в напрямку позитивної осі Y)
   * Маркер на "правій" бічній грані: ID 12 (дивиться в напрямку позитивної осі X)
   * Маркер на "задній" бічній грані: ID 13 (дивиться в напрямку негативної осі Y)
   * Маркер на "лівій" бічній грані: ID 14 (дивиться в напрямку негативної осі X)

  TO_IDs для кубика
  Оскільки всі ці 5 маркерів належать одному фізичному об'єкту (кубику), ми визначимо один TaggedObject, який містить усі ці ID маркерів.
   1 // TO_IDs: Визначає, які маркери належать до цього кубика.
   2 // Ми створюємо один тактильний об'єкт (кубик) з 5-ма маркерами.
   3 int[][] TO_IDs = {{10, 11, 12, 13, 14}};

  TO_Offsets для кубика
  Цей масив визначає 3D-позицію центру кожного маркера відносно центру кубика (0,0,0). Порядок PVector у цьому масиві повинен відповідати порядку ID маркерів у TO_IDs.
// Довжина половини сторони кубика: 0.015 метра
PVector[][] TO_Offsets = {
	{
	// Маркер 10 (верхня грань):
	// Знаходиться на 0.015м вгору від центру кубика по осі Z.
	new PVector(0, 0, 0.015),
	// Маркер 11 (передня бічна грань):
	// Знаходиться на 0.015м вперед від центру кубика по осі Y.
	new PVector(0, 0.015, 0),
	// Маркер 12 (права бічна грань):
	// Знаходиться на 0.015м вправо від центру кубика по осі X.
	new PVector(0.015, 0, 0),
	// Маркер 13 (задня бічна грань):
	// Знаходиться на 0.015м назад від центру кубика по осі Y.
	new PVector(0, -0.015, 0),
	// Маркер 14 (ліва бічна грань):
	// Знаходиться на 0.015м вліво від центру кубика по осі X.
	new PVector(-0.015, 0, 0)
	}
};


   * Чому це корисно?
       * Надійність відстеження: Наявність кількох маркерів дозволяє системі набагато надійніше відстежувати кубик, навіть якщо один або кілька маркерів тимчасово не видно камері.
       * Точна орієнтація: Система може використовувати всі 5 маркерів, щоб дуже точно визначити 3D-положення та орієнтацію кубика в просторі.
       * Визначення справжнього центру: Незважаючи на те, що ArUco маркери можуть бути розміщені по краях, ми "говоримо" системі, що "справжній" об'єкт знаходиться в центрі, і саме його позицію та орієнтацію
         потрібно використовувати для взаємодії.

  Таким чином, ці налаштування дозволять вам створити віртуальний кубик, який точно відображатиме рухи вашого фізичного кубика, використовуючи дані з 5 маркерів.

touchThreshold (Touch Threshold)

   * Призначення: Ця змінна визначає поріг відстані (у метрах) від площини екрану або поверхні, щоб система вважала, що TaggedObject "торкається" або "взаємодіє" з екранним DataObject.
   * Детальніше:
       * Значення 0.01 означає 1 сантиметр. Якщо фізичний об'єкт (його точка взаємодії, визначена TO_Offsets) знаходиться на відстані 1 см або ближче до віртуальної площини, де розташовані DataObjectи, то система реєструє "дотик".
       * Зміна чутливості:
           * Збільшення touchThreshold (наприклад, до 0.02) зробить взаємодію менш чутливою — об'єкт буде "торкатися" раніше, ще до того, як він фізично досягне поверхні.
           * Зменшення touchThreshold (наприклад, до 0.005) зробить взаємодію більш чутливою — об'єкт повинен бути ближче до поверхні, щоб спрацював "дотик".
   * Значення для системи: Ця змінна є критично важливою для визначення моменту початку та закінчення взаємодії між фізичними та віртуальними об'єктами, що дозволяє уникнути небажаних спрацьовувань або, навпаки, занадто пізньої реакції.


## **Usage & Key Controls**

* **Interaction:** Move a defined Tagged Object over an on-screen Data Object. Depending on the gestureMode, you can change the DO's value, position, and rotation.  
* **Keyboard Shortcuts:**  
  * SPACE: Reset calibration and recalculate homography.  
  * r: Reset Data Objects to their initial positions and values.  
  * 1: Set Gesture Mode 1 (e.g., rotation controls value).  
  * 2: Set Gesture Mode 2 (e.g., rotation controls value, TO controls location).  
  * 3: Set Gesture Mode 3 (e.g., TO controls location and orientation).  
  * g: Toggle Gesture debug view.  
  * t: Toggle Tag debug view (shows all active tags).  
  * d: Toggle Data Object debug view.  
  * s: Toggle Serial (console) debug messages for tag and TO events.

Режим 1: Управління значенням (Клавіша '1')
   * Опис: У цьому режимі фізичний маркер (Tagged Object) працює як ручка регулятора для екранного об'єкта (Data Object), якого він торкається.
   * Як це працює:
       * Коли ви обертаєте фізичний маркер над екранним об'єктом, його кут повороту (obj.rotation) перетворюється на числове значення.
       * Це значення встановлюється як тимчасове значення (tempVal) для екранного об'єкта.
       * Положення маркера на поверхні ігнорується; має значення лише його обертання.
Режим 2: Управління значенням та положенням (Клавіша '2')
   * Опис: Це комбінований режим, який дозволяє одночасно змінювати значення екранного об'єкта та переміщувати його по екрану.
   * Як це працює:
       1. Зміна значення: Так само, як і в Режимі 1, обертання маркера змінює числове значення (tempVal) екранного об'єкта.
       2. Зміна положення: Екранний об'єкт слідує за рухом фізичного маркера по поверхні. Код отримує 2D-координати маркера (loc2D) і оновлює положення (x, y) екранного об'єкта.
   * Призначення: Корисно для інтерактивних елементів, які потрібно переміщати і одночасно налаштовувати. Наприклад, ви можете "взяти" повзунок і, пересуваючи його, одночасно змінювати його значення обертанням.
 Режим 3: Управління положенням та орієнтацією (Клавіша '3')
   * Опис: У цьому режимі маркер повністю контролює екранний об'єкт, маніпулюючи його положенням та кутом повороту. Значення об'єкта при цьому не змінюється.
   * Як це працює:
       1. Зміна положення: Екранний об'єкт переміщується точно туди, де знаходиться фізичний маркер.
       2. Зміна орієнтації: Екранний об'єкт обертається, віддзеркалюючи обертання фізичного маркера.
   * Призначення: Цей режим призначений для прямого маніпулювання об'єктами — ніби ви тримаєте їх у руці. Наприклад, для переміщення та обертання фігур, ігрових персонажів або будь-яких графічних елементів на сцені.

## **File Overview**

* ArUcoTUI\_Client.pde: Main sketch, setup(), draw() loop, UI rendering.  
* oscEvent.pde: Handles incoming OSC messages from the detection script.  
* tools.pde: Contains calibration logic, homography calculation, and coordinate transformation functions.  
* keyEvent.pde: Defines all keyboard shortcuts.  
* Tag.pde: Class defining an individual ArUco tag.  
* TaggedObject.pde: Class defining a tangible object (a collection of one or more tags).  
* TagManager.pde: Manages all Tag and TaggedObject instances, including state updates and grouping.  
* DataObject.pde: Class for the on-screen interactive elements.  
* API.pde: Event listeners (Present, Absent, Update) that link TOs to DOs (e.g., checking for "hits").  
* ContinuousGestures.pde: Implements the logic for the different interaction modes (Mode 1, 2, 3).