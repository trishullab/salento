@echo off
path =C:\Program Files\Java\jdk1.6.0_07\bin
del *.jar
javac FileHandling.java
pause
jar cvfm FileHandling.jar manifest.mft *.class
del *.class
 