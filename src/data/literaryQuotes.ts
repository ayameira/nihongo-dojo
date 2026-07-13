// Literary Quotes Collections, keyed by target-language code
// Sources: Goodreads, iyashitour.com, various literature compilations

export interface LiteraryQuote {
  // Quote in the target language
  text: string;
  // English translation; omitted when the target language is English
  translation?: string;
  author: string;
  // Author name in the native script, when it differs from the Latin form
  authorNative?: string;
  work?: string;
  workNative?: string;
}

const japaneseQuotes: LiteraryQuote[] = [
  // ===== Natsume Soseki (夏目漱石) =====
  {
    text: '智に働けば角が立つ。情に棹させば流される。',
    translation: 'Work by reason and you grow harsh. Follow emotion and you are swept away.',
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
    work: 'Kusamakura',
    workNative: '草枕',
  },
  {
    text: 'のんきと見える人々も、心の底をたたいてみると、どこか悲しい音がする。',
    translation: 'Even people who seem carefree make a sad sound when you tap their hearts.',
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
    work: 'Kokoro',
    workNative: 'こころ',
  },
  {
    text: '吾輩は猫である。名前はまだ無い。',
    translation: 'I am a cat. As yet I have no name.',
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
    work: 'I Am a Cat',
    workNative: '吾輩は猫である',
  },
  {
    text: '真面目とはね、君、真剣勝負の意味だよ。',
    translation: 'Seriousness, my friend, means a fight to the death.',
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
    work: 'Kokoro',
    workNative: 'こころ',
  },
  {
    text: '自分の弱点をさらけ出さずに人から利益を受けられない。',
    translation: 'You cannot receive benefit from others without exposing your weaknesses.',
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
  },
  {
    text: 'あせってはいけません。ただ、牛のように、図々しく進んで行くのが大事です。',
    translation: "Don't rush. It's important to advance boldly, like an ox.",
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
  },
  {
    text: '運命は神の考えることだ。人間は人間らしく働けばそれで結構である。',
    translation: "Fate is for God to decide. It's enough for humans to work in human ways.",
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
  },
  {
    text: '月が綺麗ですね。',
    translation: 'The moon is beautiful, isn\'t it?',
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
  },
  {
    text: '自分に誠実でないものは、決して他人に誠実であり得ない。',
    translation: 'One who is not honest with himself can never be honest with others.',
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
  },
  {
    text: '世の中に片付くなんてものは殆どありゃしない。',
    translation: 'There is hardly anything in this world that gets neatly resolved.',
    author: 'Natsume Soseki',
    authorNative: '夏目漱石',
  },

  // ===== Osamu Dazai (太宰治) =====
  {
    text: '恥の多い生涯を送って来ました。',
    translation: 'Mine has been a life of much shame.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
    work: 'No Longer Human',
    workNative: '人間失格',
  },
  {
    text: '笑われて、笑われて、つよくなる。',
    translation: 'Laughed at, laughed at, I grow stronger.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
  },
  {
    text: '大人とは、裏切られた青年の姿である。',
    translation: 'An adult is the figure of a youth who has been betrayed.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
  },
  {
    text: '恋愛は、チャンスではないと思う。私はそれを意志だと思う。',
    translation: 'I think love is not chance. I believe it is will.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
  },
  {
    text: '信じられているから走るのだ。',
    translation: 'I run because I am believed in.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
    work: 'Run, Melos!',
    workNative: '走れメロス',
  },
  {
    text: '一日一日を、たっぷりと生きて行くより他は無い。',
    translation: 'There is nothing but to live each day fully.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
  },
  {
    text: '人間は、しばしば希望にあざむかれるが、しかし、また、「絶望」という観念にも同様にあざむかれる事がある。',
    translation: 'Humans are often deceived by hope, but also deceived by the concept of despair.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
  },
  {
    text: '幸福の便りというものは、待っている時には決して来ないものだ。',
    translation: 'News of happiness never comes while you are waiting for it.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
  },
  {
    text: '弱虫は、幸福をさえおそれるものです。',
    translation: 'Cowards are afraid even of happiness.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
    work: 'No Longer Human',
    workNative: '人間失格',
  },
  {
    text: '人間、失格。もはや、自分は、完全に、人間で無くなりました。',
    translation: 'Disqualified as a human being. I am no longer completely human.',
    author: 'Osamu Dazai',
    authorNative: '太宰治',
    work: 'No Longer Human',
    workNative: '人間失格',
  },

  // ===== Yukio Mishima (三島由紀夫) =====
  {
    text: '本当の美とは人を黙らせるものであります。',
    translation: 'True beauty is something that silences people.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
  },
  {
    text: '人間はあやまちを犯してはじめて真理を知る。',
    translation: 'Humans know truth only after making mistakes.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
  },
  {
    text: '空虚な目標であれ、目標をめざして努力する過程にしか人間の幸福は存在しない。',
    translation: 'Human happiness exists only in the process of striving toward goals, however empty.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
  },
  {
    text: '傷つきやすい人間ほど、複雑な鎧帷子を身につけるものだ。',
    translation: 'The more easily hurt a person is, the more complex the armor they wear.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
  },
  {
    text: '永遠に手に入らないもの、それこそが理想なのだ。',
    translation: 'That which can never be obtained—that is the ideal.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
    work: 'The Temple of the Golden Pavilion',
    workNative: '金閣寺',
  },
  {
    text: '現状維持というのは、つねに醜悪な思想である。',
    translation: 'Maintaining the status quo is always an ugly idea.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
  },
  {
    text: 'そもそも男の人生にとって大きな悲劇は、女性というものを誤解することである。',
    translation: "The greatest tragedy in a man's life is misunderstanding women.",
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
  },
  {
    text: '言葉が足りないのは、愛が足りないからだ。',
    translation: 'A lack of words is a lack of love.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
  },
  {
    text: '完全な幸福は、永遠にやって来ない。なぜならそれは幸福でなくなるからだ。',
    translation: 'Complete happiness never comes, because it would cease to be happiness.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
  },
  {
    text: '美しい死が、芸術的に見て、人生最大の傑作である。',
    translation: 'A beautiful death is, artistically, the greatest masterpiece of life.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
  },

  // ===== Yasunari Kawabata (川端康成) =====
  {
    text: '国境の長いトンネルを抜けると雪国であった。',
    translation: 'The train came out of the long tunnel into the snow country.',
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
    work: 'Snow Country',
    workNative: '雪国',
  },
  {
    text: '別れる男に、花の名を一つは教えておきなさい。花は関係がない時も関係がある。',
    translation: 'Teach a parting man the name of one flower. Flowers matter even when nothing else does.',
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
  },
  {
    text: '人の世の旅路とは、やがて消えゆく足あとのようなものである。',
    translation: "The journey of human life is like footprints that will soon disappear.",
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
  },
  {
    text: '美しい日本の私。',
    translation: 'Japan, the Beautiful, and Myself.',
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
    work: 'Nobel Prize Lecture',
    workNative: 'ノーベル賞受賞講演',
  },
  {
    text: '死んだ人の美しさというものは、この世のものではない。',
    translation: 'The beauty of the dead is not of this world.',
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
  },
  {
    text: '美しさと哀しみとが相通じるというのが日本の美の伝統である。',
    translation: 'The tradition of Japanese beauty is that beauty and sadness are intertwined.',
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
  },
  {
    text: '人間の心の底にあるのは悲しみである。',
    translation: 'At the bottom of the human heart lies sadness.',
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
  },
  {
    text: '夕焼けが美しい時には、明日は晴れる。',
    translation: 'When the sunset is beautiful, tomorrow will be clear.',
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
  },
  {
    text: '少女の目に涙が光っていた。その涙の美しさは彼を打った。',
    translation: "Tears glistened in the girl's eyes. Their beauty struck him.",
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
    work: 'Snow Country',
    workNative: '雪国',
  },
  {
    text: '駅のホームに立つと、いつも旅に出たくなる。',
    translation: 'Standing on a station platform always makes me want to travel.',
    author: 'Yasunari Kawabata',
    authorNative: '川端康成',
  },

  // ===== Haruki Murakami (村上春樹) =====
  {
    text: '希望があるところには必ず試練があるものだから。',
    translation: 'Where there is hope, there is always trial.',
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
  },
  {
    text: '深刻になることは必ずしも、真実に近づくことではない。',
    translation: "Seriousness doesn't necessarily bring you closer to truth.",
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
  },
  {
    text: 'どんなに壁が正しくてどんなに卵がまちがっていても、私は卵の側に立ちます。',
    translation: "No matter how right the wall or wrong the egg, I stand with the egg.",
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
    work: 'Jerusalem Prize Speech',
  },
  {
    text: '僕らはとても不完全な存在だし、何から何まで要領よくうまくやることなんて不可能だ。',
    translation: "We are imperfect beings, and it's impossible to do everything skillfully.",
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
  },
  {
    text: '痛みは避けられないが、苦しみは選択できる。',
    translation: 'Pain is inevitable. Suffering is optional.',
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
    work: 'What I Talk About When I Talk About Running',
    workNative: '走ることについて語るときに僕の語ること',
  },
  {
    text: '死は生の対極としてではなく、その一部として存在している。',
    translation: 'Death exists not as the opposite of life, but as a part of it.',
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
    work: 'Norwegian Wood',
    workNative: 'ノルウェイの森',
  },
  {
    text: '嵐の中でも立っていられる木になれ。',
    translation: 'Become a tree that can stand in a storm.',
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
  },
  {
    text: '世界は広い。でも自分の世界はいつも自分で作るものだ。',
    translation: 'The world is wide. But your own world is always something you create yourself.',
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
  },
  {
    text: '完璧な文章などといったものは存在しない。完璧な絶望が存在しないようにね。',
    translation: 'There is no such thing as perfect writing, just as there is no perfect despair.',
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
    work: 'Hear the Wind Sing',
    workNative: '風の歌を聴け',
  },
  {
    text: '記憶というのはいつも不完全なものだ。',
    translation: 'Memory is always incomplete.',
    author: 'Haruki Murakami',
    authorNative: '村上春樹',
  },

  // ===== Ryunosuke Akutagawa (芥川龍之介) =====
  {
    text: '人生は一箱のマッチに似ている。重大に扱うのはばかばかしい。重大に扱わねば危険である。',
    translation: 'Life resembles a matchbox. Treating it seriously is absurd. Not treating it seriously is dangerous.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },
  {
    text: '阿呆はいつも彼以外のものを阿呆であると信じている。',
    translation: 'A fool always believes everyone else is a fool.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },
  {
    text: '幸福とは幸福を問題にしない時をいう。',
    translation: 'Happiness means the time when happiness is not a question.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },
  {
    text: '自由は山巓の空気に似ている。どちらも弱い者には堪えることは出来ない。',
    translation: 'Freedom resembles the air on mountain peaks. Both are unbearable for the weak.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },
  {
    text: 'どうせ生きているからには、苦しいのはあたり前だと思え。',
    translation: 'Since you are alive anyway, accept suffering as natural.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },
  {
    text: '人生は地獄よりも地獄的である。',
    translation: 'Life is more hellish than hell itself.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },
  {
    text: '天才とは僅かに我々と一歩を隔てたもののことである。',
    translation: 'A genius is merely someone one step removed from us.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },
  {
    text: '人生を幸福にするためには、日常の瑣事を愛さなければならぬ。',
    translation: 'To make life happy, you must love the trivial things of everyday life.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },
  {
    text: '正義は武器に似たものである。武器は金を出せば、敵にも味方にも買われるであろう。',
    translation: 'Justice is like a weapon. A weapon can be bought by enemies and allies alike.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },
  {
    text: '我々の生活に必要な思想は、三千年前に尽きたかも知れない。',
    translation: 'The thoughts necessary for our lives may have been exhausted three thousand years ago.',
    author: 'Ryunosuke Akutagawa',
    authorNative: '芥川龍之介',
  },

  // ===== Jun'ichiro Tanizaki (谷崎潤一郎) =====
  {
    text: '美は物の陰に宿る。',
    translation: 'Beauty dwells in the shadows of things.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workNative: '陰翳礼讃',
  },
  {
    text: '我々東洋人は何でもない所に陰翳を生ぜしめて、美を創造する。',
    translation: 'We Orientals create beauty by generating shadows in places of no significance.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workNative: '陰翳礼讃',
  },
  {
    text: '光が乏しければ光が乏しいで、我々はその中に美を発見する。',
    translation: 'If light is scarce, we discover beauty within that scarcity.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workNative: '陰翳礼讃',
  },
  {
    text: '恋というものは一遍経験して置く価値のあるものだ。',
    translation: 'Love is something worth experiencing at least once.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
  },
  {
    text: '漆器の美しさは燭台の火に照らされた時に始めて発揮される。',
    translation: 'The beauty of lacquerware reveals itself only when lit by candlelight.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workNative: '陰翳礼讃',
  },
  {
    text: '西洋人は明るさを追い、我々は暗さの中に安らぎを見出す。',
    translation: 'Westerners pursue brightness; we find peace in darkness.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workNative: '陰翳礼讃',
  },
  {
    text: '美というものは常に現実の生活から発展する。',
    translation: 'Beauty always develops from real life.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
  },
  {
    text: '芸術は長く、人生は短い。',
    translation: 'Art is long, life is short.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
  },
  {
    text: '日本の美は暗がりの中にある。',
    translation: 'Japanese beauty lies in darkness.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workNative: '陰翳礼讃',
  },
  {
    text: '私たちは、いつも、闇のなかに美を見出す。',
    translation: 'We always find beauty within the darkness.',
    author: "Jun'ichiro Tanizaki",
    authorNative: '谷崎潤一郎',
  },

  // ===== Kenji Miyazawa (宮沢賢治) =====
  {
    text: '世界がぜんたい幸福にならないうちは個人の幸福はあり得ない。',
    translation: 'Individual happiness is impossible until the whole world becomes happy.',
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
  },
  {
    text: '雨ニモマケズ 風ニモマケズ',
    translation: 'Not losing to the rain, not losing to the wind.',
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
    work: 'Ame ni mo Makezu',
    workNative: '雨ニモマケズ',
  },
  {
    text: '本当の幸いは何だろう。',
    translation: 'What is true happiness?',
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
    work: 'Night on the Galactic Railroad',
    workNative: '銀河鉄道の夜',
  },
  {
    text: '銀河ステーションから銀河ステーションまで。',
    translation: 'From galaxy station to galaxy station.',
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
    work: 'Night on the Galactic Railroad',
    workNative: '銀河鉄道の夜',
  },
  {
    text: '永久の未完成これ完成である。',
    translation: 'Eternal incompleteness is completeness.',
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
  },
  {
    text: 'みんながめいめいじぶんの神さまがほんとうの神さまだというだろう。',
    translation: "Everyone will say their own god is the true god.",
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
    work: 'Night on the Galactic Railroad',
    workNative: '銀河鉄道の夜',
  },
  {
    text: '僕たちはみんな、いっしょに燃えているのだ。',
    translation: 'We are all burning together.',
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
  },
  {
    text: '求道すでに道である。',
    translation: 'Seeking the path is already the path.',
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
  },
  {
    text: '何がしあわせかわからないです。',
    translation: "I don't know what happiness is.",
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
  },
  {
    text: '僕はきっとできると思う。なぜって今朝お母さんがそういったんだから。',
    translation: "I'm sure I can do it. Because mother said so this morning.",
    author: 'Kenji Miyazawa',
    authorNative: '宮沢賢治',
  },

  // ===== Banana Yoshimoto (吉本ばなな) =====
  {
    text: '私がこの世でいちばん好きな場所は台所だと思う。',
    translation: 'I think the place I like best in this world is the kitchen.',
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
    work: 'Kitchen',
    workNative: 'キッチン',
  },
  {
    text: '人は変われる。どんな時でも変われる。',
    translation: 'People can change. They can change at any time.',
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
  },
  {
    text: '悲しみは消えない。ただ、悲しみと共に生きていく力が生まれるだけだ。',
    translation: "Sadness doesn't disappear. You just develop the strength to live with it.",
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
  },
  {
    text: '時間が何かを変える、ということはない。人が変えるのだ。',
    translation: "Time doesn't change anything. People do.",
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
  },
  {
    text: '本当に泣きたい時、涙は出ないものだ。',
    translation: 'When you truly want to cry, tears don\'t come.',
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
  },
  {
    text: '生きているというだけで、それは奇跡なのだ。',
    translation: 'Just being alive is a miracle.',
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
  },
  {
    text: '孤独は人を強くする。',
    translation: 'Solitude makes people stronger.',
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
  },
  {
    text: '人生には時々、静けさが必要だ。',
    translation: 'Life sometimes needs stillness.',
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
  },
  {
    text: '思い出は、心の中で生き続ける。',
    translation: 'Memories continue to live in the heart.',
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
  },
  {
    text: '愛する人を失っても、愛は消えない。',
    translation: 'Even if you lose someone you love, the love doesn\'t disappear.',
    author: 'Banana Yoshimoto',
    authorNative: '吉本ばなな',
  },

  // ===== Kobo Abe (安部公房) =====
  {
    text: '砂の中に女がいた。',
    translation: 'There was a woman in the sand.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
    work: 'The Woman in the Dunes',
    workNative: '砂の女',
  },
  {
    text: '逃げることは、必ずしも負けることではない。',
    translation: 'Fleeing is not necessarily losing.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
  },
  {
    text: '人間とは、絶えず自分自身から逃れようとする存在である。',
    translation: 'Humans are beings constantly trying to escape from themselves.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
  },
  {
    text: '壁は自由を奪うが、同時に安全も与える。',
    translation: 'Walls take away freedom, but at the same time provide safety.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
  },
  {
    text: '砂は絶えず動いている。止まることを知らない。',
    translation: 'Sand is constantly moving. It knows no stillness.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
    work: 'The Woman in the Dunes',
    workNative: '砂の女',
  },
  {
    text: '存在するということは、他者に認められることである。',
    translation: 'To exist is to be recognized by others.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
  },
  {
    text: '現実と幻想の境界は、思っているほど明確ではない。',
    translation: 'The boundary between reality and illusion is not as clear as we think.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
  },
  {
    text: '日常こそが、最も不思議なものである。',
    translation: 'The everyday is the most mysterious thing.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
  },
  {
    text: '自由とは、選択する能力のことだ。',
    translation: 'Freedom is the ability to choose.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
  },
  {
    text: '人は誰でも、どこかで道に迷っている。',
    translation: 'Everyone is lost somewhere along the way.',
    author: 'Kobo Abe',
    authorNative: '安部公房',
  },

  // ===== Kenzaburo Oe (大江健三郎) =====
  {
    text: '希望を持つことは、生きることの意味を見出すことだ。',
    translation: 'To have hope is to find meaning in life.',
    author: 'Kenzaburo Oe',
    authorNative: '大江健三郎',
  },
  {
    text: '文学は、人間の魂を救うためにある。',
    translation: 'Literature exists to save the human soul.',
    author: 'Kenzaburo Oe',
    authorNative: '大江健三郎',
  },
  {
    text: '障害を持つ息子から、私は多くのことを学んだ。',
    translation: 'I learned many things from my son with disabilities.',
    author: 'Kenzaburo Oe',
    authorNative: '大江健三郎',
  },
  {
    text: '人間の尊厳は、どんな困難にも負けない。',
    translation: 'Human dignity is not defeated by any hardship.',
    author: 'Kenzaburo Oe',
    authorNative: '大江健三郎',
  },
  {
    text: '平和は、努力によってのみ実現される。',
    translation: 'Peace can only be achieved through effort.',
    author: 'Kenzaburo Oe',
    authorNative: '大江健三郎',
  },

  // ===== Sei Shonagon (清少納言) =====
  {
    text: '春はあけぼの。やうやう白くなりゆく山際、少し明かりて、紫だちたる雲の細くたなびきたる。',
    translation: 'In spring, the dawn—when the slowly paling mountain rim is tinged with red, and wisps of purplish cloud float by.',
    author: 'Sei Shonagon',
    authorNative: '清少納言',
    work: 'The Pillow Book',
    workNative: '枕草子',
  },
  {
    text: '夏は夜。月のころはさらなり。',
    translation: 'In summer, the night. Especially when the moon shines.',
    author: 'Sei Shonagon',
    authorNative: '清少納言',
    work: 'The Pillow Book',
    workNative: '枕草子',
  },
  {
    text: '秋は夕暮れ。',
    translation: 'In autumn, the evening.',
    author: 'Sei Shonagon',
    authorNative: '清少納言',
    work: 'The Pillow Book',
    workNative: '枕草子',
  },
  {
    text: '冬はつとめて。',
    translation: 'In winter, the early morning.',
    author: 'Sei Shonagon',
    authorNative: '清少納言',
    work: 'The Pillow Book',
    workNative: '枕草子',
  },
  {
    text: 'ただ過ぎに過ぐるもの。帆かけたる舟。人の齢。',
    translation: 'Things that pass by swiftly: a boat with its sails up; the years of one\'s life.',
    author: 'Sei Shonagon',
    authorNative: '清少納言',
    work: 'The Pillow Book',
    workNative: '枕草子',
  },

  // ===== Murasaki Shikibu (紫式部) =====
  {
    text: 'いづれの御時にか、女御、更衣あまたさぶらひたまひける中に。',
    translation: 'In a certain reign there was a lady not of the first rank whom the emperor loved more than any of the others.',
    author: 'Murasaki Shikibu',
    authorNative: '紫式部',
    work: 'The Tale of Genji',
    workNative: '源氏物語',
  },
  {
    text: '世の中に絶えて桜のなかりせば春の心はのどけからまし。',
    translation: 'If there were no cherry blossoms in this world, how peaceful spring would be.',
    author: 'Ariwara no Narihira',
    authorNative: '在原業平',
    work: 'The Tales of Ise',
    workNative: '伊勢物語',
  },
  {
    text: '月日は百代の過客にして、行かふ年も又旅人也。',
    translation: 'The months and days are travelers of eternity, as are the years that pass by.',
    author: 'Matsuo Basho',
    authorNative: '松尾芭蕉',
    work: 'The Narrow Road to the Deep North',
    workNative: '奥の細道',
  },
  {
    text: '古池や蛙飛びこむ水の音。',
    translation: 'An old pond. A frog jumps in. The sound of water.',
    author: 'Matsuo Basho',
    authorNative: '松尾芭蕉',
  },
  {
    text: '夏草や兵どもが夢の跡。',
    translation: 'Summer grasses—all that remains of warriors\' dreams.',
    author: 'Matsuo Basho',
    authorNative: '松尾芭蕉',
  },

  // ===== Additional Modern Authors =====
  {
    text: '本には魂がある。大切にされた本には必ず魂がある。',
    translation: 'Books have souls. A cherished book always has a soul.',
    author: 'Sosuke Natsukawa',
    authorNative: '夏川草介',
    work: 'The Cat Who Saved Books',
    workNative: '本を守ろうとする猫の話',
  },
  {
    text: '人間は結局、大きな猿が直立歩行しているだけなのに、ずいぶんと威張っている。',
    translation: 'Humans are basically upright-walking monkeys, yet they are so full of themselves.',
    author: 'Hiro Arikawa',
    authorNative: '有川浩',
    work: 'The Travelling Cat Chronicles',
    workNative: '旅猫リポート',
  },
  {
    text: '極端な状況に置かれると、人は小さなことに気を取られて現実から逃避しようとする。',
    translation: 'In extreme situations, people escape reality by getting caught up in small details.',
    author: 'Ryu Murakami',
    authorNative: '村上龍',
    work: 'In the Miso Soup',
    workNative: 'イン ザ・ミソスープ',
  },
  {
    text: '若い人は自分にとって新しいことは誰にとっても新しいと考えがちだ。',
    translation: 'Young people tend to think what is new to them is new to everyone.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
    work: 'After the Banquet',
    workNative: '宴のあと',
  },
  {
    text: '明らかに永遠に片手で触れ、人生に他の手で触れることは不可能である。',
    translation: 'It is clearly impossible to touch eternity with one hand and life with the other.',
    author: 'Yukio Mishima',
    authorNative: '三島由紀夫',
    work: 'The Temple of the Golden Pavilion',
    workNative: '金閣寺',
  },
];

const englishQuotes: LiteraryQuote[] = [
  // ===== William Shakespeare =====
  {
    text: "All the world's a stage, and all the men and women merely players.",
    author: 'William Shakespeare',
    work: 'As You Like It',
  },
  {
    text: 'There is nothing either good or bad, but thinking makes it so.',
    author: 'William Shakespeare',
    work: 'Hamlet',
  },
  {
    text: 'The fool doth think he is wise, but the wise man knows himself to be a fool.',
    author: 'William Shakespeare',
    work: 'As You Like It',
  },
  {
    text: 'Our doubts are traitors, and make us lose the good we oft might win, by fearing to attempt.',
    author: 'William Shakespeare',
    work: 'Measure for Measure',
  },
  {
    text: 'Love all, trust a few, do wrong to none.',
    author: 'William Shakespeare',
    work: "All's Well That Ends Well",
  },

  // ===== Jane Austen =====
  {
    text: 'It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.',
    author: 'Jane Austen',
    work: 'Pride and Prejudice',
  },
  {
    text: 'The person, be it gentleman or lady, who has not pleasure in a good novel, must be intolerably stupid.',
    author: 'Jane Austen',
    work: 'Northanger Abbey',
  },

  // ===== Charles Dickens =====
  {
    text: 'It was the best of times, it was the worst of times.',
    author: 'Charles Dickens',
    work: 'A Tale of Two Cities',
  },
  {
    text: 'No one is useless in this world who lightens the burdens of another.',
    author: 'Charles Dickens',
    work: 'Our Mutual Friend',
  },

  // ===== Oscar Wilde =====
  {
    text: 'We are all in the gutter, but some of us are looking at the stars.',
    author: 'Oscar Wilde',
    work: "Lady Windermere's Fan",
  },
  {
    text: 'The truth is rarely pure and never simple.',
    author: 'Oscar Wilde',
    work: 'The Importance of Being Earnest',
  },
  {
    text: 'I can resist everything except temptation.',
    author: 'Oscar Wilde',
    work: "Lady Windermere's Fan",
  },

  // ===== Virginia Woolf =====
  {
    text: 'One cannot think well, love well, sleep well, if one has not dined well.',
    author: 'Virginia Woolf',
    work: "A Room of One's Own",
  },
  {
    text: 'No need to hurry. No need to sparkle. No need to be anybody but oneself.',
    author: 'Virginia Woolf',
    work: "A Room of One's Own",
  },

  // ===== More novelists and poets =====
  {
    text: 'Perhaps one did not want to be loved so much as to be understood.',
    author: 'George Orwell',
    work: 'Nineteen Eighty-Four',
  },
  {
    text: "Truth is stranger than fiction, but it is because Fiction is obliged to stick to possibilities; Truth isn't.",
    author: 'Mark Twain',
    work: 'Following the Equator',
  },
  {
    text: 'Hope is the thing with feathers that perches in the soul.',
    author: 'Emily Dickinson',
    work: '"Hope" is the thing with feathers',
  },
  {
    text: 'Do I contradict myself? Very well then I contradict myself. I am large, I contain multitudes.',
    author: 'Walt Whitman',
    work: 'Song of Myself',
  },
  {
    text: 'It is better to fail in originality than to succeed in imitation.',
    author: 'Herman Melville',
    work: 'Hawthorne and His Mosses',
  },
  {
    text: 'The world breaks every one and afterward many are strong at the broken places.',
    author: 'Ernest Hemingway',
    work: 'A Farewell to Arms',
  },
  {
    text: 'So we beat on, boats against the current, borne back ceaselessly into the past.',
    author: 'F. Scott Fitzgerald',
    work: 'The Great Gatsby',
  },
  {
    text: 'A man of genius makes no mistakes. His errors are volitional and are the portals of discovery.',
    author: 'James Joyce',
    work: 'Ulysses',
  },
  {
    text: "And now that you don't have to be perfect, you can be good.",
    author: 'John Steinbeck',
    work: 'East of Eden',
  },
  {
    text: 'I took a deep breath and listened to the old brag of my heart. I am, I am, I am.',
    author: 'Sylvia Plath',
    work: 'The Bell Jar',
  },
  {
    text: 'Not all those who wander are lost.',
    author: 'J.R.R. Tolkien',
    work: 'The Fellowship of the Ring',
  },
  {
    text: 'What do we live for, if it is not to make life less difficult to each other?',
    author: 'George Eliot',
    work: 'Middlemarch',
  },
  {
    text: 'I went to the woods because I wished to live deliberately, to front only the essential facts of life.',
    author: 'Henry David Thoreau',
    work: 'Walden',
  },
  {
    text: 'You may not control all the events that happen to you, but you can decide not to be reduced by them.',
    author: 'Maya Angelou',
    work: 'Letter to My Daughter',
  },
  {
    text: "If there's a book that you want to read, but it hasn't been written yet, then you must write it.",
    author: 'Toni Morrison',
  },
  {
    text: 'I am no bird; and no net ensnares me: I am a free human being with an independent will.',
    author: 'Charlotte Brontë',
    work: 'Jane Eyre',
  },
];

const frenchQuotes: LiteraryQuote[] = [
  // ===== Antoine de Saint-Exupéry =====
  {
    text: "On ne voit bien qu'avec le cœur. L'essentiel est invisible pour les yeux.",
    translation: 'One sees clearly only with the heart. What is essential is invisible to the eyes.',
    author: 'Antoine de Saint-Exupéry',
    work: 'Le Petit Prince',
  },
  {
    text: 'Tu deviens responsable pour toujours de ce que tu as apprivoisé.',
    translation: 'You become responsible, forever, for what you have tamed.',
    author: 'Antoine de Saint-Exupéry',
    work: 'Le Petit Prince',
  },
  {
    text: "Aimer, ce n'est pas se regarder l'un l'autre, c'est regarder ensemble dans la même direction.",
    translation: 'To love is not to gaze at each other, but to look together in the same direction.',
    author: 'Antoine de Saint-Exupéry',
    work: 'Terre des hommes',
  },

  // ===== Albert Camus =====
  {
    text: "Au milieu de l'hiver, j'apprenais enfin qu'il y avait en moi un été invincible.",
    translation: 'In the depths of winter, I finally learned that within me there lay an invincible summer.',
    author: 'Albert Camus',
    work: 'Retour à Tipasa',
  },
  {
    text: 'Il faut imaginer Sisyphe heureux.',
    translation: 'One must imagine Sisyphus happy.',
    author: 'Albert Camus',
    work: 'Le Mythe de Sisyphe',
  },
  {
    text: "La vraie générosité envers l'avenir consiste à tout donner au présent.",
    translation: 'Real generosity toward the future lies in giving everything to the present.',
    author: 'Albert Camus',
    work: "L'Homme révolté",
  },

  // ===== Victor Hugo =====
  {
    text: "On résiste à l'invasion des armées ; on ne résiste pas à l'invasion des idées.",
    translation: 'One can resist the invasion of armies; one cannot resist the invasion of ideas.',
    author: 'Victor Hugo',
    work: "Histoire d'un crime",
  },
  {
    text: "Le suprême bonheur de la vie, c'est la conviction qu'on est aimé.",
    translation: 'The supreme happiness of life is the conviction that one is loved.',
    author: 'Victor Hugo',
    work: 'Les Misérables',
  },
  {
    text: "La musique exprime ce qui ne peut être dit et sur quoi il est impossible de rester silencieux.",
    translation: 'Music expresses that which cannot be said and on which it is impossible to remain silent.',
    author: 'Victor Hugo',
    work: 'William Shakespeare',
  },

  // ===== Marcel Proust =====
  {
    text: 'Le véritable voyage de découverte ne consiste pas à chercher de nouveaux paysages, mais à avoir de nouveaux yeux.',
    translation: 'The real voyage of discovery consists not in seeking new landscapes, but in having new eyes.',
    author: 'Marcel Proust',
    work: 'La Prisonnière',
  },
  {
    text: "Le bonheur est salutaire pour le corps, mais c'est le chagrin qui développe les forces de l'esprit.",
    translation: 'Happiness is good for the body, but it is grief that develops the powers of the mind.',
    author: 'Marcel Proust',
    work: 'Le Temps retrouvé',
  },

  // ===== Voltaire =====
  {
    text: 'Il faut cultiver notre jardin.',
    translation: 'We must cultivate our garden.',
    author: 'Voltaire',
    work: 'Candide',
  },
  {
    text: "Le doute n'est pas un état bien agréable, mais l'assurance est un état ridicule.",
    translation: 'Doubt is not a pleasant state, but certainty is a ridiculous one.',
    author: 'Voltaire',
  },

  // ===== Molière =====
  {
    text: 'Il faut manger pour vivre et non pas vivre pour manger.',
    translation: 'One must eat to live, not live to eat.',
    author: 'Molière',
    work: "L'Avare",
  },
  {
    text: "On ne meurt qu'une fois, et c'est pour si longtemps !",
    translation: 'We die only once, and for such a long time!',
    author: 'Molière',
    work: 'Le Dépit amoureux',
  },

  // ===== More novelists, poets, and philosophers =====
  {
    text: 'Il faut être toujours ivre… De vin, de poésie ou de vertu, à votre guise.',
    translation: 'You must always be drunk… On wine, on poetry, or on virtue, as you please.',
    author: 'Charles Baudelaire',
    work: 'Le Spleen de Paris',
  },
  {
    text: 'On ne naît pas femme : on le devient.',
    translation: 'One is not born, but rather becomes, a woman.',
    author: 'Simone de Beauvoir',
    work: 'Le Deuxième Sexe',
  },
  {
    text: 'Toute la sagesse humaine sera dans ces deux mots : attendre et espérer.',
    translation: 'All human wisdom is summed up in these two words: wait and hope.',
    author: 'Alexandre Dumas',
    work: 'Le Comte de Monte-Cristo',
  },
  {
    text: "L'enfer, c'est les autres.",
    translation: 'Hell is other people.',
    author: 'Jean-Paul Sartre',
    work: 'Huis clos',
  },
  {
    text: 'Je pense, donc je suis.',
    translation: 'I think, therefore I am.',
    author: 'René Descartes',
    work: 'Discours de la méthode',
  },
  {
    text: "La plus grande chose du monde, c'est de savoir être à soi.",
    translation: 'The greatest thing in the world is to know how to belong to oneself.',
    author: 'Michel de Montaigne',
    work: 'Essais',
  },
  {
    text: "Nous avons tous assez de force pour supporter les maux d'autrui.",
    translation: 'We all have strength enough to bear the misfortunes of others.',
    author: 'François de La Rochefoucauld',
    work: 'Maximes',
  },
  {
    text: "Il n'y a qu'un bonheur dans la vie, c'est d'aimer et d'être aimé.",
    translation: 'There is only one happiness in life: to love and be loved.',
    author: 'George Sand',
  },
  {
    text: 'La parole humaine est comme un chaudron fêlé où nous battons des mélodies à faire danser les ours, quand on voudrait attendrir les étoiles.',
    translation: 'Human speech is like a cracked kettle on which we hammer out tunes to make bears dance, when we long to move the stars.',
    author: 'Gustave Flaubert',
    work: 'Madame Bovary',
  },
  {
    text: "La beauté n'est que la promesse du bonheur.",
    translation: 'Beauty is only the promise of happiness.',
    author: 'Stendhal',
    work: "De l'amour",
  },
  {
    text: 'Je est un autre.',
    translation: 'I is another.',
    author: 'Arthur Rimbaud',
    work: 'Lettres du voyant',
  },
  {
    text: "Le cœur d'une mère est un abîme au fond duquel se trouve toujours un pardon.",
    translation: "A mother's heart is a deep abyss at the bottom of which you will always find forgiveness.",
    author: 'Honoré de Balzac',
  },
  {
    text: "L'homme est né libre, et partout il est dans les fers.",
    translation: 'Man is born free, and everywhere he is in chains.',
    author: 'Jean-Jacques Rousseau',
    work: 'Du contrat social',
  },
  {
    text: 'Le cœur a ses raisons que la raison ne connaît point.',
    translation: 'The heart has its reasons, of which reason knows nothing.',
    author: 'Blaise Pascal',
    work: 'Pensées',
  },
];

export const literaryQuotesByLanguage: Record<string, LiteraryQuote[]> = {
  ja: japaneseQuotes,
  en: englishQuotes,
  fr: frenchQuotes,
};

// Languages without a collection get an empty list; the quote panel stays hidden.
export const getQuotesForLanguage = (languageCode: string): LiteraryQuote[] =>
  literaryQuotesByLanguage[languageCode] ?? [];
