# Prüfprotokoll – 2026-11-01

Umgebung: Ubuntu 24.04 ARM64 / Parallels, ROS 2 Jazzy, gz-sim 8.15.0,
ros_gz 1.0.24, turtlebot3_description 2.3.6.

- Paket mit colcon erfolgreich unter /tmp/tennis-build und /tmp/tennis-install
  gebaut; finaler Standard-Launch aus dieser Installation gestartet.
- Xacro → URDF → SDF erfolgreich konvertiert. Die offizielle Description wird
  ohne lokale Kopie oder Änderung ihrer Meshes eingebunden.
- OGRE2 mit EGL: Fragment-Shader-Kompilierfehler / RenderingAPIException.
  Auch Software-Rendering brachte keinen vollständigen erfolgreichen OGRE2-Lauf.
- OGRE1, zuerst ohne Fenster, anschließend vollständiger Standard-Launch:
  Spawn erfolgreich; Gazebo und RViz gestartet, alle acht Bridges eingerichtet.
- `check_sim.py` am vollständigen Standardstart: Exit 0; LaserScan, RGB,
  CameraInfo, JointState, Odometry und Clock empfangen. Header und Odometry-Child
  korrekt, TF von odom zu base_link, Scan, Optical und beiden Rädern auflösbar.
- ROS /cmd_vel: geometry_msgs/msg/Twist, ein Bridge-Subscriber.
  Dokumentierter unstamped-Teleop-Befehl im Pseudoterminal gestartet.
- Fahrtest mit ROS-Twist, jeweils ungefähr 3 s Simulationszeit und anschließendem
  Stopp, aus freiem Startbereich:

| Kommando | Gemessene Änderung aus Odometry | Sensorupdates während Test |
|---|---|---|
| linear.x = +0.15 m/s | +0.434 m in Fahrtrichtung | 39 Scan, 57 RGB |
| linear.x = -0.15 m/s | -0.472 m in Fahrtrichtung | 38 Scan, 52 RGB |
| angular.z = +0.5 rad/s | +1.417 rad, Translation gerundet 0.000 m | 38 Scan, 57 RGB |

Die Messung belegt Antrieb, Bridge und weiterlaufende Sensorik; Odometry allein
belegt keinen schlupffreien Bodenkontakt. Visuelle Kontaktprüfung und die gesamte
Runde wurden nicht abgenommen. GUI-Prozessstart ist kein Nachweis, dass jede
RViz-Anzeige visuell kontrolliert wurde.

Erwartete Warnungen: `gz_frame_id` wird von sdformat als Erweiterung kopiert;
die tatsächlich empfangenen Frames sind korrekt. RViz verwarf zu Beginn einen
Scan mit Zeitstempel vor dem TF-Cache; der spätere TF-Test besteht.

Abnahmestand:
- A: offizielles physikalisches Modell, erfolgreicher Spawn und Fahrtest;
  visuelle Stabilität/Bodenkontakt auf Team-Laptop noch prüfen.
- B: Welt, sechs dynamische Bälle und freie Route in SDF implementiert;
  vollständige visuelle und manuelle Routenprüfung offen.
- C: Build und kompletter Ein-Aufruf-Start inklusive RViz nachgewiesen;
  gespeicherte Anzeigen müssen noch visuell abgenommen werden.
- D: Daten, Frames, TF, Twist und drei Bewegungsarten nachgewiesen;
  interaktive vollständige Fahrt am Team-Laptop bleibt offen.

## Nachtest: OGRE2 mit gefiltertem Software-EGL

Der Grafikblocker ist durch `egl/software_egl.c` umgangen. Die oben genannten
OGRE1-Tests beschreiben den früheren Stand; Standard-Engine ist jetzt OGRE2.
Getesteter Aufruf:

```bash
ros2 launch teambot_bringup sim.launch.py headless:=true software_rendering:=true
```

- Bibliothek gebaut und in lib/libsoftware_egl.so installiert.
- EGL-Protokoll: `Found Num EGL Devices: 1`,
  `EGL_MESA_device_software`, `GL_RENDERER = llvmpipe (LLVM 20.1.2, 128 bits)`.
- Gazebo läuft ohne GUI über EGL; RViz-Prozess läuft mit Software-GL.
- check_sim.py: Exit 0, alle Topics, Header und TF geprüft.
- RGB: 320×240, Wertebereich 11–249, kein schwarzes oder uniformes Bild.
- Scan: 321 endliche Rückgaben.
- Kein systemweites LD_PRELOAD; nur Gazebo erhält die Filterbibliothek.
- Die ursprüngliche Variante mit ausschließlich RTLD_NEXT konnte Ogres lokal
  geladene EGL-Symbole nicht auflösen; behoben durch gezieltes Laden von libEGL.so.1.
- Kamera auf 10 Hz reduziert, um die CPU-Last zu begrenzen.

Die vollständige manuelle Runde und visuelle Abnahme bleiben offen.

## Erneute Prüfung mit Ogre 2 Headless

- Frischer isolierter Symlink-Build unter `/tmp/tennis-ogre2-build` und
  `/tmp/tennis-ogre2-install`: erfolgreich.
- Start mit `gui:=false rviz:=false render_engine:=ogre2 headless_rendering:=true`:
  Spawn und Bridges erfolgreich, danach Abbruch mit Exit 134 beim Kamera-Rendering:
  `Fragment Program 100000001PixelShader_ps failed to compile`.
  Protokoll: `/tmp/tennis-ogre2-launch.log`.
- Zusätzlicher Versuch mit `LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe`:
  Mesa-Absturz (Exit 139). Protokoll: `/tmp/tennis-ogre2-software.log`.
- Ogre-1-Kontrolllauf ohne GUI: `check_sim.py` Exit 0, alle sechs Datenströme
  und sämtliche geprüften TF-Verbindungen vorhanden. Dies ist kein erfolgreicher
  Ogre-2-Test und keine visuelle Abnahme.
- Fehlendes Ausführungsrecht von `scripts/check_sim.py` korrigiert; der dokumentierte
  Aufruf mit `ros2 run` besteht nun auch bei Symlink-Installation.
- Versehentlich im Paket erzeugte `build/`, `install/`, `log/` reversibel nach
  `/tmp/tennis-accidental-build-backup-20261101/` verschoben. Künftig aus dem
  Workspace `~/ros2` bauen.
- Erneuter Fahrtest im Ogre-1-Kontrolllauf, je 3 s Wandzeit: vorwärts
  0.428 m, rückwärts 0.487 m, Linksdrehung +1.437 rad, Rechtsdrehung
  -1.593 rad; alle vier Bewegungsprüfungen erfolgreich.

Fahrtest auch mit OGRE2-Software-EGL wiederholt: +0.431 m vorwärts,
-0.470 m rückwärts, Drehung +1.425 rad bei gerundet 0.000 m Translation.
Während jeder Phase jeweils 38 Scan- und 38 RGB-Updates empfangen.
Prozessumgebung über /proc geprüft: Nur Gazebo hat LD_PRELOAD gesetzt;
Gazebo und RViz haben LIBGL_ALWAYS_SOFTWARE=1.
