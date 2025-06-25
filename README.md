# Topology-Automation-Using-Python
Proiect automatizare topologie folosind Python pentru lucrarea de licență


1. Proiectul conține 4 fișiere pe care le vom discuta pe rând:

 - .pylintrc este folosit pentru a configura regulile pentru pylint. 
   
 - main.py este fișierul principal de la care pornește funcționalitatea proiectului; acesta trebuie rulat pentru pornirea aplicației. (vezi mai multe în documentație)
   
 - telnet_connector.py este modulul care se ocupă cu stabilirea conexiunii și configurarea tuturor dispozitivelor, în funcție de tip. (vezi mai multe în documentație)
   
 - testbedu.yaml este un fișier esențial pentru proiect, deoarece conține datele despre toate dispozitivele folosite în topologie. (vezi mai multe în documentație)
   
 - configs/ este directorul unde configurațiile dispozitivelor vor fi salvate pe rând, în câte un fișier de tip .txt.


2. Pentru a putea rula scriptul Python, avem nevoie de următoarele:

  - link GNS3: https://gns3.com/ pentru topologie.
    
  - link PyCharm: https://www.jetbrains.com/pycharm/download/?section=linux pentru interpreter Python.
    
  - link imagine router: https://github.com/hegdepavankumar/Cisco-Images-for-GNS3-and-EVE-NG (c3725-adventerprisek9-mz.124-15.T14.image).

  - link imagine switch: https://github.com/hegdepavankumar/Cisco-Images-for-GNS3-and-EVE-NG (viosl2-adventerprisek9-m-v152_6_0_81_e-20190423.tgz).

  - link descărcare Python: https://www.python.org/downloads/.


3. Următorii pași ar fi să creăm o topologie în GNS3 folosindu-ne de imaginile descărcate și integrate în GNS3.

4. În fișierul testbedu.yaml, schimbăm datele în funcție de topologie (adăugăm porturile dispozitivelor din GNS3).

Dacă toți pașii de mai sus au fost făcuți corect, putem rula scriptul Python pentru a începe configurarea tuturor dispozitivelor din GNS3:

   python3 main.py


Adresa GitHub: https://github.com/MunteanuIonut1357/Munteanu_Ionut_Aplicatie_Practica_INFO_Licenta
