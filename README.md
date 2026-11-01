# TurtleBot3 auf dem Tennisfeld

Simulations-Meilenstein für ROS 2 Jazzy und Gazebo Harmonic (Sim 8).
Das bisher leere Paketgerüst `MSRob_Tennis` heißt jetzt `teambot_bringup`;
der Repository-Ordner darf seinen Namen behalten. Keine AGENTS.md und keine
registrierte Kategorie gefunden: Annahme **Tennisfeld mit Tennisbällen**.
Keine Navigation, SLAM oder Ballerkennung enthalten.

## Installation und Build

Auf Ubuntu 24.04 mit eingerichtetem ROS-Jazzy-APT-Repository:

```bash
sudo apt update
sudo apt install ros-jazzy-ros-gz ros-jazzy-turtlebot3-description \
  ros-jazzy-robot-state-publisher ros-jazzy-xacro ros-jazzy-rviz2 \
  ros-jazzy-teleop-twist-keyboard python3-colcon-common-extensions python3-rosdep \
  libegl-dev libegl-mesa0 libgl1-mesa-dri
cd ~/ros2
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select teambot_bringup
source install/setup.bash
```

`~/ros2` ist ein Beispiel für den Workspace-Pfad. Bei einem alten Build des
ursprünglichen Paketgerüsts keine alte `MSRob_Tennis`-Installation zusätzlich sourcen.
Alle Laufzeitdateien werden über ament installiert; Ressourcenpfade werden im Launch
über den Paketindex aufgelöst. Keine Downloads von Gazebo Fuel erforderlich.

## Start aus frischen Terminals

Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2
source install/setup.bash
ros2 launch teambot_bringup sim.launch.py
```

Dies startet Welt, Roboter, robot_state_publisher, Bridges und RViz.
Standard ist OGRE2. Auf der Parallels-ARM-VM diesen getesteten Software-Modus verwenden:

```bash
ros2 launch teambot_bringup sim.launch.py headless:=true software_rendering:=true
```

Gazebo läuft dabei ohne GUI, Kamera und GPU-LiDAR werden weiterhin gerendert;
RViz bleibt sichtbar. Die installierte `libsoftware_egl.so` filtert die EGL-Geräteliste
auf `EGL_MESA_device_software`. `LIBGL_ALWAYS_SOFTWARE=1` und `LD_PRELOAD` gelten
nur für Gazebo; RViz erhält separat nur `LIBGL_ALWAYS_SOFTWARE=1`.
Der Filter ist lokal in `egl/software_egl.c` implementiert, da die erwähnte
Quelldatei aus dem anderen Projekt hier nicht vorlag. Keine Gazebo-/OGRE-Downgrades.

Terminal 2, interaktives Terminal erforderlich:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
  -p stamped:=false -p speed:=0.2 -p turn:=0.5 -p repeat_rate:=10.0 -p key_timeout:=0.6
```

`i`: vorwärts, `,`: rückwärts, `j`/`l`: auf der Stelle drehen, `k`: Stopp.
Teleop sendet ausdrücklich **geometry_msgs/msg/Twist**, unstamped. Die Bridge
wandelt genau diesen Typ nach gz.msgs.Twist für DiffDrive um. Kein TwistStamped-Relay.

Ohne Gazebo-Fenster mit EGL auf geeigneter Hardware:

```bash
ros2 launch teambot_bringup sim.launch.py headless:=true
```

`rviz:=false` deaktiviert zusätzlich RViz. `headless:=true` aktiviert sowohl
Serverbetrieb (`-s`) als auch `--headless-rendering`; EGL benötigt dann kein X,
das sichtbare RViz dagegen schon. Software-Rendering erfordert hier
`headless:=true` und `render_engine:=ogre2`.

Die älteren Optionen `gui:=false` (nur Server, ohne EGL) und
`headless_rendering:=true` bleiben verfügbar. OGRE1 kann explizit mit
`render_engine:=ogre` gewählt werden; nicht mit EGL kombinieren.

Bei parallelen Simulationen **zusätzlich** zu verschiedenen ROS_DOMAIN_ID jeweils
unterschiedliche `GZ_PARTITION` setzen: Gazebo-Transport wird nicht durch ROS-Domains isoliert.

## Modell und Umgebung

Waffle Pi wegen vorhandener RGB-Kamera gewählt. Die offizielle, installierte
TurtleBot3-Description (ROBOTIS, Apache 2.0) liefert Meshes, Kollisionen, Massen,
Trägheiten und Radgelenke. Unser Xacro inkludiert sie und ergänzt ausschließlich
Harmonic-Sensoren, DiffDrive und JointStatePublisher. Gazebo und
robot_state_publisher erhalten dieselbe expandierte URDF. Passive Stützen haben
reduzierte Reibung; die beiden angetriebenen Räder haben 33 mm Radius und 288 mm Spur.
Start bei Weltposition (-14, -7, 0.02), Blickrichtung +X; die geringe Fallhöhe
vermeidet anfängliche Bodendurchdringung.

Das Feld misst 23.77 × 10.97 m, der befahrbare Boden 36 × 22 m. Linien sind
reine Visuals, keine Stolperkanten. Ein kollidierendes Netz liegt bei X=0 bis
Y=±5.485; an beiden Enden ist Platz zum Umfahren. Sechs separate dynamische
Tennisbälle: Radius 33.5 mm, Masse 57 g, Kugelkollision und gelbgrünes Visual.
Positionen: (-12,-6.5), (-8,-3), (5,2), (9,-4), (1,7), (-4,4).
Kamera: 320×240, 10 Hz, rund 62° horizontal, vorne etwa 10 cm über Boden.
Erster Ball liegt vor dem Start. Gleichmäßiges Umgebungs- und Sonnenlicht;
für spätere Erkennung sollten Bälle aus wenigen Metern Abstand betrachtet werden.
Laser: 360 Messungen, 10 Hz, 0.12–20 m. Tennisbälle liegen unter der Laserebene;
für spätere Ballerkennung ist die Kamera vorgesehen.

## Topics und TF

| ROS-Topic | ROS-Typ | Frame |
|---|---|---|
| /cmd_vel | geometry_msgs/msg/Twist | körperrelative Geschwindigkeit |
| /clock | rosgraph_msgs/msg/Clock | – |
| /odom | nav_msgs/msg/Odometry | odom; child: base_footprint |
| /scan | sensor_msgs/msg/LaserScan | base_scan |
| /camera/image_raw | sensor_msgs/msg/Image | camera_rgb_optical_frame |
| /camera/camera_info | sensor_msgs/msg/CameraInfo | camera_rgb_optical_frame |
| /joint_states | sensor_msgs/msg/JointState | Radgelenke |
| /tf, /tf_static | tf2_msgs/msg/TFMessage | siehe unten |

```text
odom                       Gazebo DiffDrive → Bridge /tf
└── base_footprint
    └── base_link          robot_state_publisher
        ├── wheel_left_link / wheel_right_link (aus /joint_states)
        ├── caster_back_left_link / caster_back_right_link
        ├── imu_link (nur Frame, kein IMU-Stream)
        ├── base_scan
        └── camera_link
            └── camera_rgb_frame
                └── camera_rgb_optical_frame
```

Optical: Z vorwärts, X rechts, Y unten; offizielle optische Rotation etwa
RPY=(-π/2,0,-π/2). Sensoren melden ausdrücklich den passenden ROS-Frame,
auch wenn Gazebo feste Links intern zusammenfasst. Nur DiffDrive publiziert
odom→base_footprint; nur robot_state_publisher die restlichen Verbindungen.
Keine World-Pose-TF-Bridge und kein zweiter Joint-State-Publisher.
RViz Fixed Frame ist `odom`; absolute Startkoordinaten der Welt sind kein map-Frame.
ROS-Publisher und RViz verwenden Simulationszeit, /clock wird einseitig gebridged.

## Abnahme A–D

Nach laufendem Launch, weiteres gesourctes Terminal:

```bash
ros2 run teambot_bringup check_sim.py
ros2 topic list -t
ros2 topic info /cmd_vel -v
ros2 topic echo /odom --once
ros2 topic echo /scan --once --field header
ros2 topic echo /camera/camera_info --once --field header
ros2 run tf2_ros tf2_echo odom camera_rgb_optical_frame
ros2 run tf2_ros tf2_echo odom wheel_left_link
ros2 param get /robot_state_publisher use_sim_time
```

Der Read-only-Prüfer wartet maximal 45 Sekunden auf alle sechs Datenströme und
TF bis zu Sensoren und Rädern; falsche Frames oder fehlende Daten führen zu Exit 1.
Zusätzlich prüft er 320×240 Pixel, nichtschwarzen/nichtuniformen Bildinhalt und
mindestens einen endlichen LiDAR-Messwert.
A: In Gazebo Stillstand, Bodenkontakt, zusammenhängende Bauteile und Räder
kontrollieren. B: Feld, Netz, sechs Bälle und freie Umfahrung ansehen;
Kamerabild des ersten Balls in RViz prüfen. C: Ein-Aufruf-Start, RobotModel,
TF, Scan und Image in RViz ohne Fehler kontrollieren. D: Topic-Typen und
Frames mit obigen Befehlen prüfen; beim Fahren Odometry und Sensoraktualisierung beobachten.
`ros2 topic hz /scan` und `ros2 topic hz /camera/image_raw` zeigen die tatsächlich
realisierte Rate; langsame Rechner können unter Echtzeit laufen.

Manueller Fahrtest: Erst kurze Vorwärts-/Rückwärtsfahrt und Drehung in beide
Richtungen. Dann entlang der Welt-Wegpunkte (-14,-7) → (14,-7) → (14,7)
→ (-14,7) → (-14,-7) fahren. Jeweils vor der Ecke stoppen und auf der Stelle
drehen. Die Route umfährt das Netz; Bälle nicht überfahren. Zum Schluss Position
und Ausrichtung mit dem Start vergleichen und im Stillstand auf Drift achten.
Bei 0.2 m/s dauert die vollständige Runde einige Minuten. Kein autonomes Folgen.

## Tatsächliche Prüfung und Einschränkungen

Build lokal erfolgreich auf Jazzy / Harmonic 8.15, ARM-Parallels-VM.
Mit `headless:=true software_rendering:=true` nachgewiesen: OGRE2 über EGL,
Mesa-Softwaregerät und llvmpipe, sichtbarer RViz-Prozess, alle Topics und TF.
Kamerainhalt 320×240 mit Helligkeitswerten 11–249, LiDAR mit 321 endlichen
Messwerten. Der frühere OGRE2-Fehler ohne Gerätefilter ist damit umgangen.
Details und frühere OGRE1-Fahrtests stehen in `VALIDATION.md`.
Software-Rendering beansprucht die CPU; Echtzeitgeschwindigkeit ist nicht garantiert.

Das Modell stammt aus dem Jazzy-Paket; upstream-Abmessungen sind keine kalibrierte
Hardware-Dynamik. Netz ist eine geschlossene dünne Kollisionsbox, Bälle haben
keine Filztextur. Ballkontakte und Schlupf sind vereinfachte Physik. Noch keine
Kalibrierung oder garantierte Erkennungsentfernung. Die vollständige manuelle
Runde und visuelle Abnahme auf jedem Team-Laptop bleiben erforderlich.
