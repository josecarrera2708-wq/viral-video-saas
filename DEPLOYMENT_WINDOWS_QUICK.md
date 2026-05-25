# Deployment Automático en Windows - VERSIÓN RÁPIDA

## Requisitos (5 minutos)

Necesitas estas herramientas instaladas:
- [ ] **Docker Desktop** - https://www.docker.com/products/docker-desktop
- [ ] **Terraform** - https://www.terraform.io/downloads
- [ ] **AWS CLI** - https://aws.amazon.com/cli/
- [ ] **Git Bash o WSL2** - (Git viene con Git Bash)

Verifica que funcionan:
```powershell
docker --version
terraform --version
aws --version
git --version
```

## Paso 1: Obtener Credenciales de AWS (5 minutos)

1. Ve a https://console.aws.amazon.com/
2. Inicia sesión (crea cuenta si no tienes)
3. Ve a **IAM** > **Users** > **Create User**
4. Nombre: `viral-video-deployer`
5. Permisos: Adjunta `AdministratorAccess` (más tarde puedes restringir)
6. Ve a **Security Credentials** y copia:
   - Access Key ID
   - Secret Access Key

**Guarda estos valores en lugar seguro** - los usarás en el siguiente paso.

## Paso 2: Ejecutar Deployment (30 minutos)

Abre PowerShell en tu proyecto y ejecuta:

```powershell
# Navega a tu proyecto
cd C:\Users\mario\viral-video-saas

# Ejecuta el script de deployment
.\deploy-automated-windows.ps1
```

El script te pedirá:
1. AWS Access Key ID (pégalo)
2. AWS Secret Access Key (pégalo)
3. AWS Region (presiona Enter para `us-east-1`)

Luego el script hace TODO automáticamente:
- ✅ Configura AWS CLI
- ✅ Builds Docker images
- ✅ Pushes a AWS ECR
- ✅ Corre Terraform
- ✅ Crea RDS, Redis, S3, CloudFront
- ✅ Configura ECS services

**Tiempo total**: ~30 minutos de tu tiempo + 10-15 minutos que esperes AWS

## Paso 3: Agregue API Keys (5 minutos)

Después que el deployment termine:

1. Ve a AWS Console > **Secrets Manager**
2. Busca: `viral-video/prod/secrets`
3. Edita el secret
4. Agrega:
   - `STRIPE_SECRET_KEY`: Tu key de Stripe (obtén en https://dashboard.stripe.com/)
   - `KLING_API_KEY`: Tu key de Kling (obtén en https://kling.kuaishou.com/api)

## Paso 4: Valida que Funciona (5 minutos)

```powershell
.\post-deployment-validation.ps1
```

El script:
- Verifica que tu API responde
- Verifica que tu Frontend carga
- Verifica que la BD está conectada
- Verifica que los certificados SSL funcionan

Si todo está verde ✓ = **¡Estás listo para usar!**

## Paso 5: Primera Prueba (30 minutos)

1. Obtén tu URL del API Load Balancer:
   - AWS Console > EC2 > Load Balancers
   - Busca `viral-video-alb`
   - Copia su DNS Name

2. Copia esa URL en tu navegador (será algo como `http://viral-video-alb-123.us-east-1.elb.amazonaws.com`)

3. Prueba:
   - Signup: Crea una cuenta
   - Login: Inicia sesión
   - Create Video: Sube una imagen
   - Payment: Compra créditos (usa tarjeta test: `4242 4242 4242 4242`)
   - Download: Descarga el video

Si todo funciona = **¡Tu app está viva en AWS!**

## Costos Estimados

| Servicio | Precio/Mes |
|----------|-----------|
| ECS Fargate | $30-50 |
| RDS PostgreSQL | $40-50 |
| Redis Cache | $20 |
| S3 Storage | $12 |
| CloudFront CDN | $8-15 |
| Load Balancer | $16 |
| **TOTAL** | **$140-170** |

*Notas: Puedes reducir costos usando instancias más pequeñas. El free tier de AWS no cubre todo, pero si es tu primer AWS, tienes $300 de crédito.*

## Solución de Problemas

### Error: "AWS CLI not configured"
```powershell
aws configure
# Pega credentials cuando lo pida
```

### Error: "Docker daemon not running"
- Abre Docker Desktop
- Espera 30 segundos
- Intenta de nuevo

### Error: "Terraform apply failed"
- Lee el error completo
- Verifica que tu Access Key es correcto
- Intenta nuevamente (a veces AWS tiene transient failures)

### RDS toma demasiado tiempo
- Normal: Crear RDS toma 10-15 minutos
- Monitorea en AWS Console > RDS
- **No canceles** - déjalo terminando

### Los tasks de ECS no inician
```powershell
# Ver logs
aws logs tail /ecs/viral-backend --follow

# Ver task details
aws ecs describe-tasks --cluster viral-video-prod --tasks {task-id}
```

## Próximos Pasos Después del Deployment

### Día 1: Validación
- ✅ Signup/login funciona
- ✅ Crear video funciona (sin Kling key aún)
- ✅ Pagos funcionan (modo test Stripe)
- ✅ Descargar video funciona
- ✅ CloudWatch logs muestran actividad

### Día 2-3: Configuración Final
- Agregar tu dominio (opcional)
- Configurar HTTPS/SSL (ACM)
- Setup monitoring alerts
- Documentar runbook

### Día 4-7: Soft Launch
- Invitar 50 beta users
- Monitorear metrics
- Recopilar feedback
- Fix críticas issues

### Semana 2: GA Launch
- Marketing
- Monitor costs
- Iterate based on feedback

## Support

Si algo falla:
1. Verifica que todos los prereqs están instalados: `docker --version`, `terraform --version`, `aws --version`
2. Verifica tus AWS credentials: `aws sts get-caller-identity`
3. Revisa los logs de CloudWatch
4. Intenta correr el script de nuevo (a veces AWS necesita reintentar)

## Comando Rápido

Si solo quieres ejecutar deployment:

```powershell
cd C:\Users\mario\viral-video-saas
.\deploy-automated-windows.ps1
```

Eso es. El script hace todo lo demás.

---

**Status**: ✅ Listo para deployment
**Tiempo total**: ~1 hora
**Resultado**: App viva en AWS, lista para usuarios

**Vamos! 🚀**
