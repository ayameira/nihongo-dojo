// Japanese Literary Quotes Collection
// Sources: Goodreads, iyashitour.com, various Japanese literature compilations

export interface LiteraryQuote {
  jp: string;
  en: string;
  author: string;
  authorJp: string;
  work?: string;
  workJp?: string;
}

export const literaryQuotes: LiteraryQuote[] = [
  // ===== Natsume Soseki (夏目漱石) =====
  {
    jp: '智に働けば角が立つ。情に棹させば流される。',
    en: 'Work by reason and you grow harsh. Follow emotion and you are swept away.',
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
    work: 'Kusamakura',
    workJp: '草枕',
  },
  {
    jp: 'のんきと見える人々も、心の底をたたいてみると、どこか悲しい音がする。',
    en: 'Even people who seem carefree make a sad sound when you tap their hearts.',
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
    work: 'Kokoro',
    workJp: 'こころ',
  },
  {
    jp: '吾輩は猫である。名前はまだ無い。',
    en: 'I am a cat. As yet I have no name.',
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
    work: 'I Am a Cat',
    workJp: '吾輩は猫である',
  },
  {
    jp: '真面目とはね、君、真剣勝負の意味だよ。',
    en: 'Seriousness, my friend, means a fight to the death.',
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
    work: 'Kokoro',
    workJp: 'こころ',
  },
  {
    jp: '自分の弱点をさらけ出さずに人から利益を受けられない。',
    en: 'You cannot receive benefit from others without exposing your weaknesses.',
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
  },
  {
    jp: 'あせってはいけません。ただ、牛のように、図々しく進んで行くのが大事です。',
    en: "Don't rush. It's important to advance boldly, like an ox.",
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
  },
  {
    jp: '運命は神の考えることだ。人間は人間らしく働けばそれで結構である。',
    en: "Fate is for God to decide. It's enough for humans to work in human ways.",
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
  },
  {
    jp: '月が綺麗ですね。',
    en: 'The moon is beautiful, isn\'t it?',
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
  },
  {
    jp: '自分に誠実でないものは、決して他人に誠実であり得ない。',
    en: 'One who is not honest with himself can never be honest with others.',
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
  },
  {
    jp: '世の中に片付くなんてものは殆どありゃしない。',
    en: 'There is hardly anything in this world that gets neatly resolved.',
    author: 'Natsume Soseki',
    authorJp: '夏目漱石',
  },

  // ===== Osamu Dazai (太宰治) =====
  {
    jp: '恥の多い生涯を送って来ました。',
    en: 'Mine has been a life of much shame.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
    work: 'No Longer Human',
    workJp: '人間失格',
  },
  {
    jp: '笑われて、笑われて、つよくなる。',
    en: 'Laughed at, laughed at, I grow stronger.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
  },
  {
    jp: '大人とは、裏切られた青年の姿である。',
    en: 'An adult is the figure of a youth who has been betrayed.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
  },
  {
    jp: '恋愛は、チャンスではないと思う。私はそれを意志だと思う。',
    en: 'I think love is not chance. I believe it is will.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
  },
  {
    jp: '信じられているから走るのだ。',
    en: 'I run because I am believed in.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
    work: 'Run, Melos!',
    workJp: '走れメロス',
  },
  {
    jp: '一日一日を、たっぷりと生きて行くより他は無い。',
    en: 'There is nothing but to live each day fully.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
  },
  {
    jp: '人間は、しばしば希望にあざむかれるが、しかし、また、「絶望」という観念にも同様にあざむかれる事がある。',
    en: 'Humans are often deceived by hope, but also deceived by the concept of despair.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
  },
  {
    jp: '幸福の便りというものは、待っている時には決して来ないものだ。',
    en: 'News of happiness never comes while you are waiting for it.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
  },
  {
    jp: '弱虫は、幸福をさえおそれるものです。',
    en: 'Cowards are afraid even of happiness.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
    work: 'No Longer Human',
    workJp: '人間失格',
  },
  {
    jp: '人間、失格。もはや、自分は、完全に、人間で無くなりました。',
    en: 'Disqualified as a human being. I am no longer completely human.',
    author: 'Osamu Dazai',
    authorJp: '太宰治',
    work: 'No Longer Human',
    workJp: '人間失格',
  },

  // ===== Yukio Mishima (三島由紀夫) =====
  {
    jp: '本当の美とは人を黙らせるものであります。',
    en: 'True beauty is something that silences people.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
  },
  {
    jp: '人間はあやまちを犯してはじめて真理を知る。',
    en: 'Humans know truth only after making mistakes.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
  },
  {
    jp: '空虚な目標であれ、目標をめざして努力する過程にしか人間の幸福は存在しない。',
    en: 'Human happiness exists only in the process of striving toward goals, however empty.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
  },
  {
    jp: '傷つきやすい人間ほど、複雑な鎧帷子を身につけるものだ。',
    en: 'The more easily hurt a person is, the more complex the armor they wear.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
  },
  {
    jp: '永遠に手に入らないもの、それこそが理想なのだ。',
    en: 'That which can never be obtained—that is the ideal.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
    work: 'The Temple of the Golden Pavilion',
    workJp: '金閣寺',
  },
  {
    jp: '現状維持というのは、つねに醜悪な思想である。',
    en: 'Maintaining the status quo is always an ugly idea.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
  },
  {
    jp: 'そもそも男の人生にとって大きな悲劇は、女性というものを誤解することである。',
    en: "The greatest tragedy in a man's life is misunderstanding women.",
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
  },
  {
    jp: '言葉が足りないのは、愛が足りないからだ。',
    en: 'A lack of words is a lack of love.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
  },
  {
    jp: '完全な幸福は、永遠にやって来ない。なぜならそれは幸福でなくなるからだ。',
    en: 'Complete happiness never comes, because it would cease to be happiness.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
  },
  {
    jp: '美しい死が、芸術的に見て、人生最大の傑作である。',
    en: 'A beautiful death is, artistically, the greatest masterpiece of life.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
  },

  // ===== Yasunari Kawabata (川端康成) =====
  {
    jp: '国境の長いトンネルを抜けると雪国であった。',
    en: 'The train came out of the long tunnel into the snow country.',
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
    work: 'Snow Country',
    workJp: '雪国',
  },
  {
    jp: '別れる男に、花の名を一つは教えておきなさい。花は関係がない時も関係がある。',
    en: 'Teach a parting man the name of one flower. Flowers matter even when nothing else does.',
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
  },
  {
    jp: '人の世の旅路とは、やがて消えゆく足あとのようなものである。',
    en: "The journey of human life is like footprints that will soon disappear.",
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
  },
  {
    jp: '美しい日本の私。',
    en: 'Japan, the Beautiful, and Myself.',
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
    work: 'Nobel Prize Lecture',
    workJp: 'ノーベル賞受賞講演',
  },
  {
    jp: '死んだ人の美しさというものは、この世のものではない。',
    en: 'The beauty of the dead is not of this world.',
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
  },
  {
    jp: '美しさと哀しみとが相通じるというのが日本の美の伝統である。',
    en: 'The tradition of Japanese beauty is that beauty and sadness are intertwined.',
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
  },
  {
    jp: '人間の心の底にあるのは悲しみである。',
    en: 'At the bottom of the human heart lies sadness.',
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
  },
  {
    jp: '夕焼けが美しい時には、明日は晴れる。',
    en: 'When the sunset is beautiful, tomorrow will be clear.',
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
  },
  {
    jp: '少女の目に涙が光っていた。その涙の美しさは彼を打った。',
    en: "Tears glistened in the girl's eyes. Their beauty struck him.",
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
    work: 'Snow Country',
    workJp: '雪国',
  },
  {
    jp: '駅のホームに立つと、いつも旅に出たくなる。',
    en: 'Standing on a station platform always makes me want to travel.',
    author: 'Yasunari Kawabata',
    authorJp: '川端康成',
  },

  // ===== Haruki Murakami (村上春樹) =====
  {
    jp: '希望があるところには必ず試練があるものだから。',
    en: 'Where there is hope, there is always trial.',
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
  },
  {
    jp: '深刻になることは必ずしも、真実に近づくことではない。',
    en: "Seriousness doesn't necessarily bring you closer to truth.",
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
  },
  {
    jp: 'どんなに壁が正しくてどんなに卵がまちがっていても、私は卵の側に立ちます。',
    en: "No matter how right the wall or wrong the egg, I stand with the egg.",
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
    work: 'Jerusalem Prize Speech',
  },
  {
    jp: '僕らはとても不完全な存在だし、何から何まで要領よくうまくやることなんて不可能だ。',
    en: "We are imperfect beings, and it's impossible to do everything skillfully.",
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
  },
  {
    jp: '痛みは避けられないが、苦しみは選択できる。',
    en: 'Pain is inevitable. Suffering is optional.',
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
    work: 'What I Talk About When I Talk About Running',
    workJp: '走ることについて語るときに僕の語ること',
  },
  {
    jp: '死は生の対極としてではなく、その一部として存在している。',
    en: 'Death exists not as the opposite of life, but as a part of it.',
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
    work: 'Norwegian Wood',
    workJp: 'ノルウェイの森',
  },
  {
    jp: '嵐の中でも立っていられる木になれ。',
    en: 'Become a tree that can stand in a storm.',
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
  },
  {
    jp: '世界は広い。でも自分の世界はいつも自分で作るものだ。',
    en: 'The world is wide. But your own world is always something you create yourself.',
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
  },
  {
    jp: '完璧な文章などといったものは存在しない。完璧な絶望が存在しないようにね。',
    en: 'There is no such thing as perfect writing, just as there is no perfect despair.',
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
    work: 'Hear the Wind Sing',
    workJp: '風の歌を聴け',
  },
  {
    jp: '記憶というのはいつも不完全なものだ。',
    en: 'Memory is always incomplete.',
    author: 'Haruki Murakami',
    authorJp: '村上春樹',
  },

  // ===== Ryunosuke Akutagawa (芥川龍之介) =====
  {
    jp: '人生は一箱のマッチに似ている。重大に扱うのはばかばかしい。重大に扱わねば危険である。',
    en: 'Life resembles a matchbox. Treating it seriously is absurd. Not treating it seriously is dangerous.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },
  {
    jp: '阿呆はいつも彼以外のものを阿呆であると信じている。',
    en: 'A fool always believes everyone else is a fool.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },
  {
    jp: '幸福とは幸福を問題にしない時をいう。',
    en: 'Happiness means the time when happiness is not a question.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },
  {
    jp: '自由は山巓の空気に似ている。どちらも弱い者には堪えることは出来ない。',
    en: 'Freedom resembles the air on mountain peaks. Both are unbearable for the weak.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },
  {
    jp: 'どうせ生きているからには、苦しいのはあたり前だと思え。',
    en: 'Since you are alive anyway, accept suffering as natural.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },
  {
    jp: '人生は地獄よりも地獄的である。',
    en: 'Life is more hellish than hell itself.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },
  {
    jp: '天才とは僅かに我々と一歩を隔てたもののことである。',
    en: 'A genius is merely someone one step removed from us.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },
  {
    jp: '人生を幸福にするためには、日常の瑣事を愛さなければならぬ。',
    en: 'To make life happy, you must love the trivial things of everyday life.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },
  {
    jp: '正義は武器に似たものである。武器は金を出せば、敵にも味方にも買われるであろう。',
    en: 'Justice is like a weapon. A weapon can be bought by enemies and allies alike.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },
  {
    jp: '我々の生活に必要な思想は、三千年前に尽きたかも知れない。',
    en: 'The thoughts necessary for our lives may have been exhausted three thousand years ago.',
    author: 'Ryunosuke Akutagawa',
    authorJp: '芥川龍之介',
  },

  // ===== Jun'ichiro Tanizaki (谷崎潤一郎) =====
  {
    jp: '美は物の陰に宿る。',
    en: 'Beauty dwells in the shadows of things.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workJp: '陰翳礼讃',
  },
  {
    jp: '我々東洋人は何でもない所に陰翳を生ぜしめて、美を創造する。',
    en: 'We Orientals create beauty by generating shadows in places of no significance.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workJp: '陰翳礼讃',
  },
  {
    jp: '光が乏しければ光が乏しいで、我々はその中に美を発見する。',
    en: 'If light is scarce, we discover beauty within that scarcity.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workJp: '陰翳礼讃',
  },
  {
    jp: '恋というものは一遍経験して置く価値のあるものだ。',
    en: 'Love is something worth experiencing at least once.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
  },
  {
    jp: '漆器の美しさは燭台の火に照らされた時に始めて発揮される。',
    en: 'The beauty of lacquerware reveals itself only when lit by candlelight.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workJp: '陰翳礼讃',
  },
  {
    jp: '西洋人は明るさを追い、我々は暗さの中に安らぎを見出す。',
    en: 'Westerners pursue brightness; we find peace in darkness.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workJp: '陰翳礼讃',
  },
  {
    jp: '美というものは常に現実の生活から発展する。',
    en: 'Beauty always develops from real life.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
  },
  {
    jp: '芸術は長く、人生は短い。',
    en: 'Art is long, life is short.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
  },
  {
    jp: '日本の美は暗がりの中にある。',
    en: 'Japanese beauty lies in darkness.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
    work: 'In Praise of Shadows',
    workJp: '陰翳礼讃',
  },
  {
    jp: '私たちは、いつも、闇のなかに美を見出す。',
    en: 'We always find beauty within the darkness.',
    author: "Jun'ichiro Tanizaki",
    authorJp: '谷崎潤一郎',
  },

  // ===== Kenji Miyazawa (宮沢賢治) =====
  {
    jp: '世界がぜんたい幸福にならないうちは個人の幸福はあり得ない。',
    en: 'Individual happiness is impossible until the whole world becomes happy.',
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
  },
  {
    jp: '雨ニモマケズ 風ニモマケズ',
    en: 'Not losing to the rain, not losing to the wind.',
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
    work: 'Ame ni mo Makezu',
    workJp: '雨ニモマケズ',
  },
  {
    jp: '本当の幸いは何だろう。',
    en: 'What is true happiness?',
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
    work: 'Night on the Galactic Railroad',
    workJp: '銀河鉄道の夜',
  },
  {
    jp: '銀河ステーションから銀河ステーションまで。',
    en: 'From galaxy station to galaxy station.',
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
    work: 'Night on the Galactic Railroad',
    workJp: '銀河鉄道の夜',
  },
  {
    jp: '永久の未完成これ完成である。',
    en: 'Eternal incompleteness is completeness.',
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
  },
  {
    jp: 'みんながめいめいじぶんの神さまがほんとうの神さまだというだろう。',
    en: "Everyone will say their own god is the true god.",
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
    work: 'Night on the Galactic Railroad',
    workJp: '銀河鉄道の夜',
  },
  {
    jp: '僕たちはみんな、いっしょに燃えているのだ。',
    en: 'We are all burning together.',
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
  },
  {
    jp: '求道すでに道である。',
    en: 'Seeking the path is already the path.',
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
  },
  {
    jp: '何がしあわせかわからないです。',
    en: "I don't know what happiness is.",
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
  },
  {
    jp: '僕はきっとできると思う。なぜって今朝お母さんがそういったんだから。',
    en: "I'm sure I can do it. Because mother said so this morning.",
    author: 'Kenji Miyazawa',
    authorJp: '宮沢賢治',
  },

  // ===== Banana Yoshimoto (吉本ばなな) =====
  {
    jp: '私がこの世でいちばん好きな場所は台所だと思う。',
    en: 'I think the place I like best in this world is the kitchen.',
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
    work: 'Kitchen',
    workJp: 'キッチン',
  },
  {
    jp: '人は変われる。どんな時でも変われる。',
    en: 'People can change. They can change at any time.',
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
  },
  {
    jp: '悲しみは消えない。ただ、悲しみと共に生きていく力が生まれるだけだ。',
    en: "Sadness doesn't disappear. You just develop the strength to live with it.",
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
  },
  {
    jp: '時間が何かを変える、ということはない。人が変えるのだ。',
    en: "Time doesn't change anything. People do.",
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
  },
  {
    jp: '本当に泣きたい時、涙は出ないものだ。',
    en: 'When you truly want to cry, tears don\'t come.',
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
  },
  {
    jp: '生きているというだけで、それは奇跡なのだ。',
    en: 'Just being alive is a miracle.',
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
  },
  {
    jp: '孤独は人を強くする。',
    en: 'Solitude makes people stronger.',
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
  },
  {
    jp: '人生には時々、静けさが必要だ。',
    en: 'Life sometimes needs stillness.',
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
  },
  {
    jp: '思い出は、心の中で生き続ける。',
    en: 'Memories continue to live in the heart.',
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
  },
  {
    jp: '愛する人を失っても、愛は消えない。',
    en: 'Even if you lose someone you love, the love doesn\'t disappear.',
    author: 'Banana Yoshimoto',
    authorJp: '吉本ばなな',
  },

  // ===== Kobo Abe (安部公房) =====
  {
    jp: '砂の中に女がいた。',
    en: 'There was a woman in the sand.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
    work: 'The Woman in the Dunes',
    workJp: '砂の女',
  },
  {
    jp: '逃げることは、必ずしも負けることではない。',
    en: 'Fleeing is not necessarily losing.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
  },
  {
    jp: '人間とは、絶えず自分自身から逃れようとする存在である。',
    en: 'Humans are beings constantly trying to escape from themselves.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
  },
  {
    jp: '壁は自由を奪うが、同時に安全も与える。',
    en: 'Walls take away freedom, but at the same time provide safety.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
  },
  {
    jp: '砂は絶えず動いている。止まることを知らない。',
    en: 'Sand is constantly moving. It knows no stillness.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
    work: 'The Woman in the Dunes',
    workJp: '砂の女',
  },
  {
    jp: '存在するということは、他者に認められることである。',
    en: 'To exist is to be recognized by others.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
  },
  {
    jp: '現実と幻想の境界は、思っているほど明確ではない。',
    en: 'The boundary between reality and illusion is not as clear as we think.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
  },
  {
    jp: '日常こそが、最も不思議なものである。',
    en: 'The everyday is the most mysterious thing.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
  },
  {
    jp: '自由とは、選択する能力のことだ。',
    en: 'Freedom is the ability to choose.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
  },
  {
    jp: '人は誰でも、どこかで道に迷っている。',
    en: 'Everyone is lost somewhere along the way.',
    author: 'Kobo Abe',
    authorJp: '安部公房',
  },

  // ===== Kenzaburo Oe (大江健三郎) =====
  {
    jp: '希望を持つことは、生きることの意味を見出すことだ。',
    en: 'To have hope is to find meaning in life.',
    author: 'Kenzaburo Oe',
    authorJp: '大江健三郎',
  },
  {
    jp: '文学は、人間の魂を救うためにある。',
    en: 'Literature exists to save the human soul.',
    author: 'Kenzaburo Oe',
    authorJp: '大江健三郎',
  },
  {
    jp: '障害を持つ息子から、私は多くのことを学んだ。',
    en: 'I learned many things from my son with disabilities.',
    author: 'Kenzaburo Oe',
    authorJp: '大江健三郎',
  },
  {
    jp: '人間の尊厳は、どんな困難にも負けない。',
    en: 'Human dignity is not defeated by any hardship.',
    author: 'Kenzaburo Oe',
    authorJp: '大江健三郎',
  },
  {
    jp: '平和は、努力によってのみ実現される。',
    en: 'Peace can only be achieved through effort.',
    author: 'Kenzaburo Oe',
    authorJp: '大江健三郎',
  },

  // ===== Sei Shonagon (清少納言) =====
  {
    jp: '春はあけぼの。やうやう白くなりゆく山際、少し明かりて、紫だちたる雲の細くたなびきたる。',
    en: 'In spring, the dawn—when the slowly paling mountain rim is tinged with red, and wisps of purplish cloud float by.',
    author: 'Sei Shonagon',
    authorJp: '清少納言',
    work: 'The Pillow Book',
    workJp: '枕草子',
  },
  {
    jp: '夏は夜。月のころはさらなり。',
    en: 'In summer, the night. Especially when the moon shines.',
    author: 'Sei Shonagon',
    authorJp: '清少納言',
    work: 'The Pillow Book',
    workJp: '枕草子',
  },
  {
    jp: '秋は夕暮れ。',
    en: 'In autumn, the evening.',
    author: 'Sei Shonagon',
    authorJp: '清少納言',
    work: 'The Pillow Book',
    workJp: '枕草子',
  },
  {
    jp: '冬はつとめて。',
    en: 'In winter, the early morning.',
    author: 'Sei Shonagon',
    authorJp: '清少納言',
    work: 'The Pillow Book',
    workJp: '枕草子',
  },
  {
    jp: 'ただ過ぎに過ぐるもの。帆かけたる舟。人の齢。',
    en: 'Things that pass by swiftly: a boat with its sails up; the years of one\'s life.',
    author: 'Sei Shonagon',
    authorJp: '清少納言',
    work: 'The Pillow Book',
    workJp: '枕草子',
  },

  // ===== Murasaki Shikibu (紫式部) =====
  {
    jp: 'いづれの御時にか、女御、更衣あまたさぶらひたまひける中に。',
    en: 'In a certain reign there was a lady not of the first rank whom the emperor loved more than any of the others.',
    author: 'Murasaki Shikibu',
    authorJp: '紫式部',
    work: 'The Tale of Genji',
    workJp: '源氏物語',
  },
  {
    jp: '世の中に絶えて桜のなかりせば春の心はのどけからまし。',
    en: 'If there were no cherry blossoms in this world, how peaceful spring would be.',
    author: 'Ariwara no Narihira',
    authorJp: '在原業平',
    work: 'The Tales of Ise',
    workJp: '伊勢物語',
  },
  {
    jp: '月日は百代の過客にして、行かふ年も又旅人也。',
    en: 'The months and days are travelers of eternity, as are the years that pass by.',
    author: 'Matsuo Basho',
    authorJp: '松尾芭蕉',
    work: 'The Narrow Road to the Deep North',
    workJp: '奥の細道',
  },
  {
    jp: '古池や蛙飛びこむ水の音。',
    en: 'An old pond. A frog jumps in. The sound of water.',
    author: 'Matsuo Basho',
    authorJp: '松尾芭蕉',
  },
  {
    jp: '夏草や兵どもが夢の跡。',
    en: 'Summer grasses—all that remains of warriors\' dreams.',
    author: 'Matsuo Basho',
    authorJp: '松尾芭蕉',
  },

  // ===== Additional Modern Authors =====
  {
    jp: '本には魂がある。大切にされた本には必ず魂がある。',
    en: 'Books have souls. A cherished book always has a soul.',
    author: 'Sosuke Natsukawa',
    authorJp: '夏川草介',
    work: 'The Cat Who Saved Books',
    workJp: '本を守ろうとする猫の話',
  },
  {
    jp: '人間は結局、大きな猿が直立歩行しているだけなのに、ずいぶんと威張っている。',
    en: 'Humans are basically upright-walking monkeys, yet they are so full of themselves.',
    author: 'Hiro Arikawa',
    authorJp: '有川浩',
    work: 'The Travelling Cat Chronicles',
    workJp: '旅猫リポート',
  },
  {
    jp: '極端な状況に置かれると、人は小さなことに気を取られて現実から逃避しようとする。',
    en: 'In extreme situations, people escape reality by getting caught up in small details.',
    author: 'Ryu Murakami',
    authorJp: '村上龍',
    work: 'In the Miso Soup',
    workJp: 'イン ザ・ミソスープ',
  },
  {
    jp: '若い人は自分にとって新しいことは誰にとっても新しいと考えがちだ。',
    en: 'Young people tend to think what is new to them is new to everyone.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
    work: 'After the Banquet',
    workJp: '宴のあと',
  },
  {
    jp: '明らかに永遠に片手で触れ、人生に他の手で触れることは不可能である。',
    en: 'It is clearly impossible to touch eternity with one hand and life with the other.',
    author: 'Yukio Mishima',
    authorJp: '三島由紀夫',
    work: 'The Temple of the Golden Pavilion',
    workJp: '金閣寺',
  },
];

// Helper to get a random quote
export const getRandomQuote = (): LiteraryQuote => {
  return literaryQuotes[Math.floor(Math.random() * literaryQuotes.length)];
};

// Helper to get quote by author
export const getQuotesByAuthor = (authorJp: string): LiteraryQuote[] => {
  return literaryQuotes.filter(q => q.authorJp === authorJp);
};
