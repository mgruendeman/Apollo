import { Link } from 'react-router-dom'

// How to use the site: listening, following the transcript, reacting, and
// reporting mistakes. Linked from the home page and each mission's player.
export default function Guide() {
  return (
    <div className="page guide">
      <Link to="/" className="back-link">
        ← All missions
      </Link>
      <header className="mission-header">
        <p className="eyebrow">How to use this site</p>
        <h1>Listening to Apollo</h1>
        <p className="lede">
          Every mission here is told in the crew&apos;s own voices, from NASA&apos;s recordings, with the conversation
          written out alongside so you can follow who&apos;s speaking and what they mean.
        </p>
      </header>

      <section>
        <h2>Two ways to listen</h2>
        <dl className="guide-list">
          <dt>Whole mission</dt>
          <dd>
            NASA&apos;s own tapes, played end to end from before launch to splashdown. Drag the bar to go anywhere in the
            mission, or pick a moment from the timeline below the player. Shaded stretches of the bar are where there&apos;s
            a recording. (Apollo 11 so far, with more missions on the way.)
          </dd>
          <dt>Highlight clips</dt>
          <dd>
            Short clips of the mission&apos;s key moments, each with its photos. Tick &ldquo;Keep playing through the
            mission&rdquo; to run from one to the next.
          </dd>
        </dl>
        <h3>Switches on the player</h3>
        <dl className="guide-list">
          <dt>Real time</dt>
          <dd>
            Off, the silent stretches between recordings are skipped. On, they count by at their true length, so the
            mission unfolds as it happened: start at launch and listen along, or use &ldquo;Happening right now&rdquo; on a
            mission&apos;s anniversary to hear it live, the same hour it happened.
          </dd>
          <dt>Mission Control announcer</dt>
          <dd>
            The public-affairs announcer (&ldquo;This is Apollo Control&hellip;&rdquo;) who explained the mission to the
            press and public. Switch him off to hear just the crew and the ground. The tapes are the broadcast copy, with
            him and the crew on one track, so where he talks over the crew he can&apos;t be taken out; those moments are
            marked in the transcript.
          </dd>
          <dt>Fill gaps with clips</dt>
          <dd>Where NASA&apos;s tapes have no recording, a short clip of that moment plays in its place.</dd>
        </dl>
      </section>

      <section>
        <h2>Following the transcript</h2>
        <ul className="guide-points">
          <li>The line being spoken is highlighted and the transcript scrolls along with the audio.</li>
          <li>Click (or tap) a line to jump the audio to it.</li>
          <li>
            Words with a dotted underline open a short explanation from the <Link to="/glossary">glossary</Link>; a small{' '}
            <span className="info-dot">i</span> after a number or code explains that one.
          </li>
          <li>
            <strong>Talking over the crew</strong> marks where the announcer&apos;s voice covers the crew&apos;s.{' '}
            <strong>Not on this recording</strong> marks a call NASA transcribed from its full radio loop that the broadcast
            copy missed. Tap either tag for more.
          </li>
        </ul>
      </section>

      <section>
        <h2>Reactions and favorites</h2>
        <p>
          Press the <strong className="guide-key">☺+</strong> button on any line of the transcript to react to it. There are five
          reactions:
        </p>
        <ul className="guide-reactions">
          <li>🤣 Funny</li>
          <li>😲 Wow</li>
          <li>‼️ Big moment</li>
          <li>❤️ Moving</li>
          <li>😬 Tense</li>
        </ul>
        <p>
          The most-reacted lines become each mission&apos;s <em>Listener favorites</em>. In the photo gallery, tap ♥ to
          like a photo; &ldquo;Most liked&rdquo; shows the favorites. No account needed.
        </p>
      </section>

      <section id="report">
        <h2>Spotted a mistake? Tell me</h2>
        <p>
          The transcripts come from NASA&apos;s typed transcripts of the 1960s and 70s, read from scans by a computer, so
          there are misread words, wrong speakers and times that are a little off. I read every report and fix it, and a
          fix often becomes a rule that corrects the same mistake everywhere, on every mission.
        </p>
        <ol className="guide-points">
          <li>
            <strong>Press and hold the line</strong> (on a computer, right-click it).
          </li>
          <li>
            Say what&apos;s wrong in a few words: <em>&ldquo;Houston, not Horton&rdquo;</em>, <em>&ldquo;this is Aldrin,
            not Armstrong&rdquo;</em>, <em>&ldquo;there are more words after next&rdquo;</em>, <em>&ldquo;this is on the
            recording&rdquo;</em>, or <em>&ldquo;what&apos;s this?&rdquo;</em> for something that needs explaining.
          </li>
          <li>Send it. The mission, time and line go along automatically, so you don&apos;t need to copy anything.</li>
        </ol>
        <p>
          Not sure what a word should be? Say so: I check the tape before changing anything.
        </p>
        <h3>Know the story behind a moment?</h3>
        <p>
          Some lines only make sense with the story behind them: a bet, a joke, a name on the Moon. If you know one, send
          it the same way (press and hold the line) or through the <Link to="/contact">contact page</Link>, and I can add
          it to the timeline. A source makes it much easier to add: a book and page number, an interview, or a link.
        </p>
      </section>

      <section>
        <h2>Where it all comes from</h2>
        <p>
          The audio is NASA&apos;s own recordings, with background noise gently reduced. The transcripts are NASA&apos;s
          air-to-ground transcripts, timed to the audio by speech recognition and repaired from the tapes where the scan
          went wrong; the announcer&apos;s words are transcribed from the tapes themselves.
        </p>
      </section>

      <section id="use">
        <h2>Using the transcripts and photos</h2>
        <p>
          The edited transcripts and processed photos on this site are &copy; Apollo Audio Archive. You&apos;re welcome to
          use them free of charge for non-commercial purposes, such as teaching, study, research and personal projects,
          with credit to the Apollo Audio Archive and a link back to this site.
        </p>
        <p>
          Commercial use (anything sold, or used to promote something sold) needs my permission first:{' '}
          <Link to="/contact">get in touch</Link>.
        </p>
        <p>
          NASA&apos;s original recordings, transcripts and photographs are in the public domain, and none of this limits
          what you can do with those originals.
        </p>
      </section>

      <p className="guide-contact">
        Questions, ideas, a story to add, or something else? <Link to="/contact">Get in touch</Link>.
      </p>
    </div>
  )
}
