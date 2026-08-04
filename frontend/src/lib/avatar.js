import { mediaUrl } from '../api'

// Avatar por defecto de un usuario sin foto: silueta blanca sobre rojo de marca,
// como data: URI. Antes se usaba ui-avatars.com (iniciales), que exigía internet
// —la PC del gym no siempre lo tiene y ahí el avatar quedaba roto— y de paso le
// mandaba el nombre de cada socio a un tercero. Al ser un data: URI el <img>
// resuelve sin red y sin petición extra.
const SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
<rect width="24" height="24" fill="#dc2626"/>
<g transform="translate(3.6 3.6) scale(0.7)" fill="#ffffff">
<path d="M7.5 6a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0Z"/>
<path d="M3.751 20.105a8.25 8.25 0 0 1 16.498 0 .75.75 0 0 1-.437.695A18.683 18.683 0 0 1 12 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 0 1-.437-.695Z"/>
</g>
</svg>`

export const AVATAR_FALLBACK = `data:image/svg+xml,${encodeURIComponent(SVG)}`

/** src del avatar de un usuario: su foto si tiene, si no la silueta de marca. */
export function fotoSrc(u) {
  return u?.foto_url ? mediaUrl(u.foto_url) : AVATAR_FALLBACK
}
