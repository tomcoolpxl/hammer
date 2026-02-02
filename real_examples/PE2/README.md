# Automation PE2

Je maakt Ansible playbooks die een webserver en databaseserver configureren met basisinstellingen, en je gebruikt daarna lesconcepten in aparte playbooks voor loops, conditionals, retries, gebruik van vault en common variabelen.

## Environment
- Twee AlmaLinux 9 servers:
  - `server0.pxldemo.local` (webserver)
  - `server1.pxldemo.local` (database server)
- Het inventory-file `inventory.ini` is voorzien. Deze file mag niet worden aangepast.
- Template files `index.html.j2` en `httpd.conf.j2` zijn apart meegegeven. Deze files moeten niet worden aangepast.
- Geen `shell` of `command` modules gebruiken!
- Voor de extra's zijn er nog andere files meegegeven die mogelijk wel moeten worden aangepast.

## Scripts

- **`./deploy.sh`** – Zet de VMs op en runt alle playbooks
- **`./run_ansible.sh`** – Runt alle Ansible playbooks in de juiste volgorde
- **`./autograde.py`** – Python-script dat alles checkt en een eindscore berekent. Puur indicatief - dit zijn niet de echte of finale punten. Manuele checks gebeuren ook.
- **`./nuke_all_vms.sh`** - Verwijder alle bestaande/locked/dangling Vagrant/Virtualbox VMs van vorige oefeningen.

Het script autograde.py kan als volgt gerund worden:
```bash
# Volledige deployment (verwijdert en hermaakt de VMs)
./autograde.py             # zou moeten werken
python3 ./autograde.py     # alternatief
# tests runnen zonder de omgeving opnieuw op te zetten of de playbooks opnieuw te runnen.
./autograde.py --nodeploy --noansible
# tests runnen zonder de omgeving opnieuw op te zetten
./autograde.py --nodeploy
# tests runnen zonder de ansible playbooks eerst te runnen
python3 ./autograde.py --noansible
# Help info tonen
./autograde.py --help
```

Tijdens development:
```bash
./deploy.sh                                           # vms from scratch
ansible-playbook -i inventory.ini playbook_loops.yml  # aparte playbooks
./run_ansible.sh                                      # alle playbooks
./autograde.py --nodeploy --noansible                 # check status
```

Initial autograding zal gebeuren met dit commando, dat een eerst pristine omgeving opzet, dan alle playbooks runt en dan de autograding toepast. De resultaten worden weggeschreven naar een `results.csv` file.
```bash
./autograde.py
```

## Basic Requirements (50% van het totaal)

Vul het playbook `playbook.yml` aan:

1. **Projectstructuur**
   - Gebruik de `group_vars/` directory voor je variabele files.
   - Gebruik de bestaande templates in je playbooks. Je vindt ze in de `./templates` directory. Deze hoeven niet aangepast te worden.

2. **Web Server Setup**
   - Installeer Apache op `server0`.
   - Configureer Apache om te luisteren op poort `8080` via een group var en de meegegeven template `httpd.conf.j2`.
   - Maak een `index.html` pagina met de bijgeleverde template.
   - Start de Apache service en zorg dat die ook bij reboot start.

3. **Database Configuratie**
   - Installeer Chrony op `server1`.
   - Start de Chrony service en zorg dat die ook bij reboot start
   - Maak eerst de groep `mysql` en dan de gebruiker `mysql` aan die tot de groep `mysql` behoort.
   - Maak een directory `/opt/backup` met eigenaar `mysql` en groep `mysql`. De directory locatie wordt ingesteld dmv een group variable die jij defineert voor database servers.

4. **Group Vars**
   Definieer de volgende variabelen via group vars voor de juiste groepen van hosts:
   - de webserver poort `8080`
   - de database backup directory location, ingesteld op `/opt/backup`

## Extras (50%)

**Aan Extra opdrachten worden enkel punten toegekend als de basisopdracht helemaal correct is (50/50).** Als de basisopdracht niet correct is (< 50/50) krijgen de Extra opdrachten automatisch het cijfer '0'.

Gebruik aparte playbooks:

### playbook_loops.yml (10%)
- Installeer meerdere packages op de webserver in één task met een loop:
  - `httpd`
  - `httpd-tools`
  - `mod_ssl`
- Maak meerdere users aan via een loop:
  - `webadmin` (met home dir en shell `/bin/bash`)
  - `reviewer` (met home dir en shell `/bin/bash`)
  - `monitor` (met home dir en shell `/bin/bash`)

### playbook_retries.yml (10%)
- Maak een taak die probeert een file te downloaden van `https://nonexistent-domain-123456.com/file.txt` naar `/tmp/test_file.txt` op `server0`.
- Implementeer retry logic (2 retries met 1 seconde delay) voor deze taak.
- Als de download uiteindelijk faalt:
  - Het playbook mag **NIET stoppen** met een error.
  - Maak dan een file aan in `/tmp/test_file.txt` met exact de tekst "Download failed, this is a fallback file."

### playbook_common.yml (10%) 
- Definieert variabelen die gebruikt worden door **alle** servers, **via group vars**:
  - `company_name: "PXL Education"`
  - `admin_email: "admin@pxl.be"`
- Maak een file `/etc/motd` op beide servers via een jinja2-template dat toont:
  - De server hostname (dit staat al klaar in de meegegeven template)
  - De bedrijfsnaam
  - De admin email
- Gebruik hier nog 2 extra variabelen voor **alle** servers, **via group variables**.
- Er is een meegegeven jinja2 template `./templates/motd.j2` dat je kan gebruiken als aanvang.

### playbook_vault.yml (10%)
- Gebruik de file `vault.yml` in de root van het project.
- Sla een variabele `vault_secret_key` op met waarde `PXLPXL` in die file.
- Encrypt het file met ansible vault met wachtwoord `passwordpxl`.
- Gebruik de file `vars/main.yml` die de vault variabele mapped naar een gewone var:
  - `secret_key: "{{ vault_secret_key }}"`
- Laad beide var-files in je playbook.
- Maak een file `/var/www/html/secret.txt` op `server0` met de `secret_key` waarde. Niet hardcoden!
- Zorg dat enkel root het `secret.txt` file mag lezen.

### playbook_conditionals.yml (10%)
- Installeer `wget` op `server0`, MAAR ENKEL als de OS distributie exact "AlmaLinux" is én major versie exact "9". Gebruik hiervoor de ingebouwde ansible facts `ansible_distribution` en `ansible_distribution_major_version`.
- Maak een file `/etc/sysconfig/server_role` met content "webserver" als root, MAAR ENKEL als de directory `/var/www/html` bestaat. Dit check je met een conditie.

## Technical Information

### Vereiste packages
- Webservers:
  - **apache** - package name: `httpd`, service name: `httpd`
  - **wget** - package name: `wget`
- Database servers:
  - **chrony** - package name: `chrony`, service name: `chronyd`


### Mogelijke Ansible Modules
- [`ansible.builtin.dnf`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/dnf_module.html) – packages installeren en beheren
- [`ansible.builtin.template`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/template_module.html) – config templates deployen
- [`ansible.builtin.service`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/service_module.html) – services starten en inschakelen
- [`ansible.builtin.file`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html) – files/directories aanmaken en permissies instellen
- [`ansible.builtin.copy`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html) – files met content aanmaken
- [`ansible.builtin.group`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/group_module.html) – groepen aanmaken
- [`ansible.builtin.user`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/user_module.html) – user accounts aanmaken
- [`ansible.builtin.get_url`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/get_url_module.html) – files downloaden
- [`ansible.builtin.stat`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/stat_module.html) – checken of files/directories bestaan en wat hun properties zijn

### Registered Variables
- [Ansible Registered Variables](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#registering-variables)
