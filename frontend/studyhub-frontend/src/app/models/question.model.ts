export interface Question {
  id_original_json: string;
  titulo_original: string;
  enunciado_html: string;
  opcoes: Option[];
  resposta_sugerida_letra: string;
  num_answers_to_select: number;
  url_original?: string;
}

export interface Option {
  letra: string;
  letra_raw?: string;
  texto: string;
  texto_html?: string;
}