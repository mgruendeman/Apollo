import { likesAvailable, likeId, toggleLike, useLikes } from '../lib/likes'

// ♡ / ♥ with the photo's like count. Hidden where the site has no server.
export default function LikeButton({ photo }) {
  const id = likeId(photo)
  const state = useLikes([id])(id)
  if (!likesAvailable) return null
  const liked = !!state?.liked
  return (
    <button
      type="button"
      className={liked ? 'like-button is-liked' : 'like-button'}
      aria-pressed={liked}
      aria-label={liked ? 'Unlike this photo' : 'Like this photo'}
      onClick={(e) => {
        e.stopPropagation()
        toggleLike(id)
      }}
    >
      <span aria-hidden="true">{liked ? '♥' : '♡'}</span> {state ? state.count : ''}
    </button>
  )
}
