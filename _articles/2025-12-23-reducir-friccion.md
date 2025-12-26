---
layout: post
title: "Reducir fricción en entornos de trabajo distribuidos"
date: 2025-12-23
---

Trabajo con Linux. Pero también trabajo en más de un lugar.

La gran mayoría de mis días contienen una dinámica similar en la que despierto a la mañana para avanzar con mis estudios y algún proyecto. Eso lo hago en mi PC de escritorio. Luego de desayunar me dirijo a mi primer trabajo, en el que uso una computadora de la oficina en la que tengo configuradas mis credenciales de Git en la terminal. Al salir de ese trabajo, voy a un segundo trabajo, en el que utilizo mi propia notebook en la que, por supuesto, todas mis credenciales están seteadas. Finalmente, por la tarde, regreso a mi departamento a continuar con la PC de escritorio.

A veces, en el mismo día, toco el mismo repo en tres máquinas distintas. Y sucede algo tan obvio como inevitable: cada vez que me siento, hago lo mismo: git pull, git pull, git pull.

No es difícil.  
No es grave.  
Pero es ruido.

Y el ruido, repetido todos los días, termina siendo un costo real para alguien que ya debe desplegar una dinámica cotidiana en el contexto del pluriempleo.

El problema no es Git, es la fricción al empezar.

## Idea: eliminar fricción al iniciar

En cada arranque de sesión debería responder a preguntas como: “¿En qué estaba trabajando?” y no perder tiempo con preguntas como: “¿Este repo está actualizado?”.

Ese micro-check se multiplica por:
- cantidad de máquinas
- cantidad de repos
- cantidad de veces que cambio de lugar

Y se convierte en fricción cognitiva. En una condición inicial innecesaria para entrar en foco.

La idea: que mi sesión empiece siempre en un estado consistente.  

No quería un “script mágico”. Quería algo que me permitiera llevar un log, que sea seguro (no pisara cambios locales), determinista (que se ejecutara al bootear) y conveniente (que corra cuando tiene sentido, al encender la máquina).

La solución terminó siendo simple:
- una lista explícita de repos
- un check de conectividad real (DNS + HTTPS)
- un script que hace `git pull --ff-only`
- y un `systemd --user` que se ejecuta al iniciar sesión, una vez por arranque

No para “automatizar por automatizar”. Para sacar decisiones repetitivas del circuito.

## Implementación

### Lista de repos a actualizar

Creo un archivo con los repos que quiero mantener sincronizados. Uno por línea.

Archivo: `~/.config/git-autopull/repos.txt`

Ejemplo:

```text
# Repos que quiero actualizar al iniciar sesión
~/code/proyecto-laboral
~/code/proyecto-personal
~/code/otro-proyecto
```

Esto tiene una ventaja importante: el servicio no “descubre” nada.
No recorre el disco. No adivina. No toca repos que no le pedí.

Actualiza únicamente lo que yo declaré.

### Script de autopull (con checks y guard “once per boot”)

Archivo: `~/.local/bin/git-pull-repos.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

LIST_FILE="${HOME}/.config/git-autopull/repos.txt"

STATE_DIR="${HOME}/.local/state/git-autopull"
mkdir -p "${STATE_DIR}"

LOG_FILE="${STATE_DIR}/last-run.log"
BOOT_FILE="${STATE_DIR}/last-boot-id"

ts() { date -Is; }
log() { echo "[$(ts)] $*" | tee -a "${LOG_FILE}"; }

have_cmd() { command -v "$1" >/dev/null 2>&1; }

# Run once per boot
BOOT_ID="$(cat /proc/sys/kernel/random/boot_id)"
if [[ -f "${BOOT_FILE}" ]] && [[ "$(cat "${BOOT_FILE}")" == "${BOOT_ID}" ]]; then
  exit 0
fi
echo "${BOOT_ID}" > "${BOOT_FILE}"

# Conectividad robusta: DNS + HTTPS
dns_ok() {
  if have_cmd resolvectl; then
    resolvectl query github.com >/dev/null 2>&1
  else
    getent ahosts github.com >/dev/null 2>&1
  fi
}

https_ok() {
  if have_cmd curl; then
    curl -fsSIL --max-time 2 https://github.com >/dev/null 2>&1
  else
    (echo > /dev/tcp/github.com/443) >/dev/null 2>&1
  fi
}

wait_for_net() {
  local tries=12
  local i
  for i in $(seq 1 "${tries}"); do
    if dns_ok && https_ok; then
      return 0
    fi
    sleep 2
  done
  return 1
}

# Prechecks
if [[ ! -f "${LIST_FILE}" ]]; then
  log "ERROR: falta ${LIST_FILE}"
  exit 2
fi

log "START"

if ! wait_for_net; then
  log "ERROR: sin conectividad usable (DNS/HTTPS) tras varios intentos. Abort."
  exit 3
fi
log "NET OK (DNS + HTTPS)"

# Pull repos
while IFS= read -r repo_dir; do
  [[ -z "${repo_dir}" ]] && continue
  [[ "${repo_dir}" =~ ^[[:space:]]*# ]] && continue
  repo_dir="${repo_dir/#\~/$HOME}"

  if [[ ! -d "${repo_dir}/.git" ]]; then
    log "SKIP (no git repo): ${repo_dir}"
    continue
  fi

  cd "${repo_dir}"

  # Seguridad: si hay cambios locales, no tocamos nada
  if [[ -n "$(git status --porcelain)" ]]; then
    log "SKIP (dirty): ${repo_dir}"
    continue
  fi

  # Evitar casos sin upstream configurado
  if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
    log "SKIP (no upstream): ${repo_dir}"
    continue
  fi

  # Validar que el remote exista (y que auth no falle) antes de pull
  if ! git ls-remote --exit-code --heads >/dev/null 2>&1; then
    log "SKIP (remote/auth fail): ${repo_dir}"
    continue
  fi

  log "PULL: ${repo_dir}"
  git pull --ff-only | tee -a "${LOG_FILE}"

done < "${LIST_FILE}"

log "END"
```

## Instalación:

```bash
mkdir -p ~/.local/bin ~/.config/git-autopull
chmod +x ~/.local/bin/git-pull-repos.sh
```

Asegurate de que `~/.local/bin` esté incluido en tu `PATH`.  

En la mayoría de las distribuciones modernas esto ya viene configurado por defecto para sesiones de usuario.

Qué hace este script (intencionalmente):
- no hace stash
- no hace reset
- no fuerza merges
- no toca repos con cambios locales
- no inventa repos: solo actualiza los declarados

La idea es que esto sea confiable, no “agresivo”.

> Este servicio se ejecuta en segundo plano (headless) al iniciar sesión.  
> Para que funcione correctamente, Git debe poder autenticarse sin intervención humana.
>
> Si usás SSH, asegurate de que tu llave no tenga passphrase o que tu agente SSH (`ssh-agent`) esté disponible para el servicio de usuario de systemd (lo cual no siempre está garantizado en el arranque temprano).
>
> Si usás HTTPS, deberás tener configurado un `git-credential-helper` que recuerde tus credenciales.
>
> Si la autenticación falla, el script está diseñado para detectar el error con `git ls-remote` y saltar el repositorio silenciosamente (registrándolo en el log), para evitar que el proceso quede colgado esperando un input que nunca llegará.


### Servicio `systemd (user unit)`

Archivo: `~/.config/systemd/user/git-autopull.service`

```ini
[Unit]
Description=Auto git pull
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=%h/.local/bin/git-pull-repos.sh
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7

[Install]
WantedBy=default.target
```

Elegí `systemd` en lugar de `cron` porque me permite definir dependencias claras (como `network-online.target`), ejecutar la tarea una sola vez por boot (incluso si cierro y vuelvo a iniciar sesión), y contar con logs integrados y consultables mediante `journalctl`.

En este caso, el objetivo no es ejecutar una tarea “cada tanto”, sino garantizar un estado inicial consistente al comenzar a trabajar.

Activación:

```bash
mkdir -p ~/.config/systemd/user
systemctl --user daemon-reload
systemctl --user enable git-autopull.service
systemctl --user status git-autopull.service
```

Ejecutarlo manualmente (para probar sin reiniciar):

```bash
systemctl --user start git-autopull.service
```

Logs:

```bash
journalctl --user -u git-autopull.service -b
cat ~/.local/state/git-autopull/last-run.log
```

Este enfoque puede complementarse con una estructura de directorios consistente (para que “tres máquinas” se sientan como una).

La otra mitad de este problema no es el pull. Es la consistencia.

Cuando trabajás en varias máquinas, la pregunta real es: ¿dónde vive cada repo? ¿cómo lo encuentro sin pensar? ¿cómo evito que cada máquina tenga su propia “geografía”?

Una solución simple es adoptar una jerarquía estable y replicable en todas las máquinas:

```
~/code-and-studies/
  work/
    clienteA/
    clienteB/
  personal/
    tracker/
    blog/
  labs/
    experiments/
```

Así, cuando cambiás de máquina, tu cerebro no re-indexa el filesystem. Los paths son los mismos, el muscle memory es el mismo, y el script de autopull puede apuntar a rutas iguales en todos lados.

## Cierre:

Este post no es sobre Git. Es sobre fricción.

Cuando trabajás en varios lugares, tu flujo ya tiene suficiente ruido: viajes, context switching, entornos distintos. Lo mínimo que debería pasar es que, cuando abrís la terminal, el código esté donde tiene que estar.

Desde que implementé este sistema, mi rutina matutina cambió: ya no empiezo con `git pull`, empiezo con el código abierto, en el punto exacto donde lo dejé — ya sea la noche anterior, en alguno de mis trabajos, o en mi casa hace dos días. 

La automatización no es magia.
Es simplemente quitar decisiones innecesarias del camino.  

Y en un contexto de pluriempleo y múltiples máquinas, eso no es un lujo: es una necesidad.  

Si también trabajás en varios entornos, espero que esta solución te sirva. Y si tenés una variante mejor, compartila — al fin y al cabo, la ingeniería es colectiva.
