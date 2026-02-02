# Opdracht: Webserver configureren met Ansible
Je hebt 1 virtuele machine gekregen: 'server0'. Het is jouw taak om een Ansible playbook te schrijven dat nginx installeert en configureert.

## Hulpscripts

- `./deploy.sh`: zet een pristine environment op en run ansible playbook.
- `./run_ansible.sh`: run ansible playbook
- `./nuke_all_vms.sh`: verwijder resterende vagrant vms van andere oefeningen
- `./check_deploy.py`: scriptje om bestanden op de VM te checken
- `./autograde.py`: zet pristine environment op, run playbook 4x, voer tests uit en autograde. duurt lang.

## Minimum (10/20)
- Kijk ook even naar Extra 1, die kan je misschien onmiddellijk mee implementeren.
- Maak een nieuwe directory, gedefinieerd door een **variabele** `doc_root`
  - enkel als die directory nog niet bestaat.
  - Geef de waarde `/var/www/mypage` aan `doc_root`.
- Gebruik `landing-page.html.j2` om `index.html` aan te maken
  - in de directory gedefinieerd door `doc_root`.
  - De meegeleverde file `landing-page.html.j2` in deze repo mag niet aangepast worden.
  - Defineer en gebruik variabelen als nodig.
- Maak en gebruik een template `nginx.conf.j2` om een serverconfiguratiebestand op te zetten
  - in `/etc/nginx/conf.d/mypage.conf` op de vm.
  - Maak het parameteriseerbaar
  - zorg er onder meer voor dat `/var/www/` uiteindelijk ook wordt vervangen door `/var/www/mypage`.
- Installeer en run het package en service `nginx`
  - zorg ervoor dat nginx ook automatisch opstart at boot.
  - **Zorg ervoor dat Nginx herstart wordt wanneer de serverconfiguratie wordt gewijzigd.**
- Installeer en run het package en service `firewalld`
  - zorg ervoor dat firewalld ook automatisch opstart at boot.
  - Laat binnenkomend verkeer toe op poort `8080`.
    - **Gebruik de parameteriseerbare poort 8080 voor zowel de nginx configuratie als de firewalld regels, dmv van een variabele `web_port`.**
- Zorg ervoor dat je ansible playbook niet crasht.

Extra's tellen enkel mee als de minimum requirements gehaald zijn.

## Extra 1 (2 punten): Variables
- **Alle** gebruikte ansible variabelen, met de correcte namen
  - worden toegekend dmv een externe file `vars.yml`
  - die je plaatst in de root van deze repository.

## Extra 2 (4 punten): Conditionals
- Zorg ervoor dat je een taak in je playbook hebt die controleert of `index.html` al bestaat in de `doc_root` directory.
  - Als het bestand niet bestaat, gebruik dan `landing-page.html.j2` om het aan te maken.
  - Als `index.html` al wel bestaat op de remote host, sla dan deze taak over.
- Dit is een uitbreiding van de minimum requirements.

## Extra 3 (4 punten): Handler
- Sta traffic toe op de tcp-poort gedefineerd door een variabele `web_port`
  - zorg ervoor dat deze rule **permanent** wordt toegepast.
  - **Gebruik de parameteriseerbare poort 8080 voor zowel de nginx configuratie als de firewalld regels, dmv van een variabele `web_port`.**
  - Zorg ervoor dat als er wijzigingen worden aangebracht in de `firewalld` instellingen, de firewalld service wordt herstart dmv een **handler**.

## Oplevering
- Zorg dat alle bestanden ingecheckt zijn voor de deadline. Bestanden zelfs 1s na de deadline worden genegeerd. Commits na de deadline betekent ook nog eens `-2`.

## Package names
- RHEL9 package name voor nginx is 'nginx'.
- RHEL9 package name voor firewalld is 'firewalld'

## Benodigde Ansible modules
- https://docs.ansible.com/ansible/latest/collections/ansible/builtin/package_module.html
- https://docs.ansible.com/ansible/latest/collections/ansible/builtin/service_module.html
- https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html
- https://docs.ansible.com/ansible/latest/collections/ansible/builtin/stat_module.html#ansible-collections-ansible-builtin-stat-module
- https://docs.ansible.com/ansible/latest/collections/ansible/builtin/template_module.html
- https://docs.ansible.com/ansible/latest/collections/ansible/posix/firewalld_module.html

- **Je mag de `command` module enkel gebruiken voor "read-only" operaties in de plaats van `stat`**: 
https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

## Informatie over handlers, conditionals, variables
- https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_handlers.html
- https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_conditionals.html
- https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html