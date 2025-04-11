import pkg_resources
import re

# este codigo lo que hace es leer el archivo requirements.txt, para ver si estan
# todas las libreria que instalada o sea las que estan el txt
# Leer el archivo requirements.txt
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

# Obtener los paquetes instalados (Tony Mateo 23-EISN-2-044)
installed = {pkg.key for pkg in pkg_resources.working_set}

# Comprobar qué paquetes faltan (Tony Mateo 23-EISN-2-044)
missing = []
installed_packages = []

for r in requirements:
    # Eliminar comentarios y líneas vacías (Tony Mateo 23-EISN-2-044)
    r = r.strip()
    if not r or r.startswith('#'):
        continue
    
    # Obtener el nombre del paquete (sin versión) (Tony Mateo 23-EISN-2-044)
    package_name = re.split('==|>=|<=|>|<|~=', r)[0].strip()
    
    if package_name.lower() in (pkg.lower() for pkg in installed):
        installed_packages.append(r)
    else:
        missing.append(r)

print("Paquetes ya instalados:")
for pkg in installed_packages:
    print(f"  - {pkg}")

print("\nPaquetes que faltan por instalar:")
for pkg in missing:
    print(f"  - {pkg}")