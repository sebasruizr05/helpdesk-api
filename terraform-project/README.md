# Terraform Project

Infraestructura aislada para la sustentacion de Terraform.

## Servicios creados

- `VPC` con subred y reglas de firewall para SSH.
- `Compute Engine` como bastion para la conexion remota.
- `Cloud SQL for PostgreSQL` con base, usuario y password administrados por Terraform.
- `Artifact Registry` para almacenar imagenes Docker.
- `Cloud Storage` para artefactos o respaldos de apoyo.

## Estructura

- `modules/network`: VPC, subred y firewall para SSH.
- `modules/compute`: VM bastion con IP publica y cliente PostgreSQL instalado.
- `modules/database`: instancia PostgreSQL, base de datos y usuario.
- `modules/storage`: bucket y repositorio de Artifact Registry.
- `environments/*`: puntos de entrada por ambiente.
- `scripts/`: demostracion SQL para crear, poblar y eliminar datos.

## Prerrequisitos

- Terraform `>= 1.6`
- `gcloud` autenticado con permisos sobre el proyecto `helpdesk-api-492703`
- APIs habilitadas por Terraform
- llave publica SSH disponible localmente

En esta implementacion se uso:

- proyecto GCP: `helpdesk-api-492703`
- llave publica: `~/.ssh/id_rsa_terraform.pub`
- llave privada para `scp` y `ssh`: `~/.ssh/id_rsa_terraform`

Antes del despliegue conviene verificar:

```bash
gcloud auth list
gcloud config get-value project
gcloud auth application-default print-access-token >/dev/null && echo OK
ls ~/.ssh/id_rsa_terraform ~/.ssh/id_rsa_terraform.pub
```

## Despliegue

Los comandos se ejecutan localmente, no dentro de la VM. Terraform corre en la maquina del usuario y crea los recursos en GCP usando las APIs del proyecto.

Ejemplo para `dev`:

```bash
cd terraform-project/environments/dev
terraform init
terraform plan \
  -var="project_id=helpdesk-api-492703" \
  -var="ssh_public_key=$(cat ~/.ssh/id_rsa_terraform.pub)" \
  -var="db_password=DefinirClaveSeguraAqui"
terraform apply \
  -var="project_id=helpdesk-api-492703" \
  -var="ssh_public_key=$(cat ~/.ssh/id_rsa_terraform.pub)" \
  -var="db_password=DefinirClaveSeguraAqui"
```

Al finalizar el `apply`, Terraform entrega outputs como:

- `bastion_name`
- `bastion_public_ip`
- `cloud_sql_public_ip`
- `database_name`
- `database_user`

## Ejecucion de la prueba SSH + SQL

La evidencia pedida por la rubrica se cubre asi:

- conexion remota por SSH al bastion
- ejecucion de 3 scripts de base de datos
- visualizacion de datos insertados
- destruccion completa de la infraestructura con `terraform destroy`

1. Obtener la IP publica del bastion:

```bash
terraform output bastion_public_ip
```

2. Copiar los scripts SQL y el wrapper al bastion:

```bash
gcloud compute scp \
  --ssh-key-file="$HOME/.ssh/id_rsa_terraform" \
  ../../scripts/*.sql ../../scripts/run_db_demo.sh \
  bastion@$(terraform output -raw bastion_name):/tmp \
  --zone us-central1-a \
  --project helpdesk-api-492703
```

3. Abrir SSH:

```bash
gcloud compute ssh bastion@$(terraform output -raw bastion_name) \
  --ssh-key-file="$HOME/.ssh/id_rsa_terraform" \
  --zone us-central1-a \
  --project helpdesk-api-492703
```

4. Ejecutar el wrapper que corre los 3 scripts:

```bash
chmod +x /tmp/run_db_demo.sh
DB_HOST=$(terraform output -raw cloud_sql_public_ip) \
DB_NAME=$(terraform output -raw database_name) \
DB_USER=$(terraform output -raw database_user) \
DB_PASSWORD='DefinirClaveSeguraAqui' \
/tmp/run_db_demo.sh
```

El wrapper ejecuta:

- `create_schema.sql`
- `seed_and_query.sql`
- `drop_schema.sql`

La salida esperada durante la sustentacion debe mostrar:

- creacion exitosa de tablas demo
- insercion y consulta de datos en PostgreSQL
- eliminacion final de las tablas demo

## Comandos utiles de evidencia

Ver la ruta SSH sugerida:

```bash
terraform output bastion_ssh_command
```

Ver la IP publica de Cloud SQL:

```bash
terraform output cloud_sql_public_ip
```

Ver el nombre de la base y el usuario:

```bash
terraform output database_name
terraform output database_user
```

Ver todos los outputs del ambiente:

```bash
terraform output
```

## Destruccion

La eliminacion completa queda soportada con:

```bash
terraform destroy \
  -var="project_id=helpdesk-api-492703" \
  -var="ssh_public_key=$(cat ~/.ssh/id_rsa_terraform.pub)" \
  -var="db_password=DefinirClaveSeguraAqui"
```

