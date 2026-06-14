import { LiteraryCardData } from "@/components/LiteraryCard";

export const MOCK_AUTHORS: LiteraryCardData[] = [
  {
    respuesta_texto:
      "Rómulo Gallegos fue uno de los narradores más significativos de la literatura venezolana del siglo XX. Su obra explora la identidad nacional, el arraigo a la tierra y las tensiones entre la civilización y la barbarie. Su novela más reconocida, «Doña Bárbara», retrata la vida en el llano venezolano con una prosa cargada de realismo y precisión etnográfica.",
    metadata: {
      nombre: "Rómulo Gallegos",
      disciplina: "Narrativa",
      periodo: "1884–1969",
      lugar: "Caracas, Venezuela",
      imagenes: [
        "https://picsum.photos/seed/gallegos1/600/400",
        "https://picsum.photos/seed/gallegos2/600/400",
        "https://picsum.photos/seed/gallegos3/600/400",
        "https://picsum.photos/seed/gallegos4/600/400",
      ],
      audios: ["mock://audio/gallegos-voz.mp3"],
      pdfs: ["https://example.com/obras/dona-barbara.pdf"],
    },
  },
  {
    respuesta_texto:
      "Teresa de la Parra fue una de las voces más importantes de la literatura latinoamericana del siglo XX. Pionera del feminismo literario en Venezuela, su obra combina intimismo con una crítica sutil a la sociedad patriarcal y conservadora de su época. Sus novelas «Ifigenia» y «Memorias de Mamá Blanca» la consagraron como figura clave de las letras venezolanas.",
    metadata: {
      nombre: "Teresa de la Parra",
      disciplina: "Narrativa",
      periodo: "1889–1936",
      lugar: "París, Francia / Caracas, Venezuela",
      imagenes: [
        "https://picsum.photos/seed/parra1/600/400",
        "https://picsum.photos/seed/parra2/600/400",
      ],
      audios: ["mock://audio/parra-voz.mp3"],
      pdfs: ["https://example.com/obras/ifigenia.pdf"],
    },
  },
  {
    respuesta_texto:
      "Arturo Uslar Pietri es considerado uno de los escritores venezolanos más influyentes del siglo XX. Sus cuentos, ensayos y novelas, especialmente «Las lanzas coloradas», exploran la historia nacional y el realismo mágico temprano con una precisión y elegancia notables, marcando un antes y un después en la narrativa hispanoamericana.",
    metadata: {
      nombre: "Arturo Uslar Pietri",
      disciplina: "Narrativa · Ensayo",
      periodo: "1906–2001",
      lugar: "Caracas, Venezuela",
      imagenes: [
        "https://picsum.photos/seed/uslar1/600/400",
        "https://picsum.photos/seed/uslar2/600/400",
        "https://picsum.photos/seed/uslar3/600/400",
      ],
      audios: ["mock://audio/uslar-voz.mp3"],
      pdfs: ["https://example.com/obras/las-lanzas-coloradas.pdf"],
    },
  },
];

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content?: string;
  literaryCard?: LiteraryCardData;
  timestamp: Date;
  relatedQuestions?: string[];
}

export const MOCK_CONVERSATIONS = [
  {
    id: "conv-1",
    title: "¿Quién fue Rómulo Gallegos?",
    date: "Hoy",
    messages: [] as ChatMessage[],
  },
  {
    id: "conv-2",
    title: "Literatura llanera del siglo XX",
    date: "Ayer",
    messages: [] as ChatMessage[],
  },
  {
    id: "conv-3",
    title: "Autoras de Venezuela — siglo XX",
    date: "13 jun",
    messages: [] as ChatMessage[],
  },
  {
    id: "conv-4",
    title: "El costumbrismo venezolano",
    date: "12 jun",
    messages: [] as ChatMessage[],
  },
];

export const SUGGESTED_QUESTIONS = [
  "¿Quién fue Teresa de la Parra?",
  "El costumbrismo venezolano",
  "Literatura llanera del siglo XX",
  "Autoras de Venezuela",
  "¿Qué es el criollismo literario?",
  "Vanguardismo venezolano",
];

export const RELATED_QUESTIONS: Record<string, string[]> = {
  gallegos: [
    "¿Qué otras obras escribió Gallegos?",
    "¿De qué corriente literaria forma parte?",
    "Literatura venezolana del siglo XX",
  ],
  parra: [
    "¿Cuál es la novela más famosa de Teresa de la Parra?",
    "Feminismo en la literatura venezolana",
    "Escritoras contemporáneas de Teresa de la Parra",
  ],
  default: [
    "¿Cuáles son las principales corrientes literarias venezolanas?",
    "Autores de Caracas",
    "Literatura del interior de Venezuela",
  ],
};

export function getMockResponse(query: string): ChatMessage {
  const q = query.toLowerCase();
  let card: LiteraryCardData | undefined;
  let relatedQuestions: string[];

  if (q.includes("gallegos") || q.includes("romulo") || q.includes("rómulo")) {
    card = MOCK_AUTHORS[0];
    relatedQuestions = RELATED_QUESTIONS.gallegos;
  } else if (q.includes("parra") || q.includes("teresa")) {
    card = MOCK_AUTHORS[1];
    relatedQuestions = RELATED_QUESTIONS.parra;
  } else if (q.includes("uslar") || q.includes("pietri")) {
    card = MOCK_AUTHORS[2];
    relatedQuestions = RELATED_QUESTIONS.default;
  } else {
    relatedQuestions = RELATED_QUESTIONS.default;
  }

  return {
    id: `msg-${Date.now()}`,
    role: "assistant",
    content: card
      ? undefined
      : "Podría encontrar información sobre ese tema en nuestra base de datos. Por el momento, te sugiero explorar los autores y obras disponibles haciendo preguntas más específicas como «¿Quién fue Teresa de la Parra?» o «¿Qué escribió Arturo Uslar Pietri?»",
    literaryCard: card,
    timestamp: new Date(),
    relatedQuestions,
  };
}
