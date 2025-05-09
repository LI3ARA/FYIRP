from openai import OpenAI
from image_generator import LlavaGenerator
from icecream import ic

class MistralGenerator:
    def __init__(self, model="mistral", base_url="http://localhost:1234/v1", api_key="lm-studio", prompt_template=None):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.prompt_template = prompt_template or (
            "Context:\n{context}\n\n"
            "Question: {question}\n"
            "Answer:"
        )

    def generate_answer(self, question, context=""):
        prompt = self.prompt_template.format(context=context, question=question)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
    
class MultimodalAnswerPipeline:
    def __init__(self, mistral: MistralGenerator, llava: LlavaGenerator):
        self.mistral = mistral
        self.llava = llava

    def needs_visual_analysis(self, caption, question):
        detection_prompt = f"""
You are a helpful scientific assistant. Based on the caption and question below, determine if answering the question requires analyzing the visual (figure, table, graph, etc.) or if it can be answered from text alone.

Caption: "{caption}"
Question: "{question}"

Reply with only YES or NO.
"""
        response = ic(self.mistral.generate_answer(detection_prompt))
        return "yes" in response.lower()

    def synthesize_answer(self, question, caption, vlm_answer):
        synthesis_prompt = f"""
You are a scientific assistant synthesizing a final answer.

Original Question: {question}
Caption: {caption}
Visual Model's Answer: {vlm_answer}

Write a clear, complete answer based on this information.
"""
        return ic(self.mistral.generate_answer(synthesis_prompt))

    def answer_question(self, question, caption, image_path):
        if self.needs_visual_analysis(caption, question):
            vlm_answer = self.llava.generate_answer(image_path=image_path, question=question, caption=caption)
            ic(vlm_answer)
            final_answer = self.synthesize_answer(question=question, caption=caption, vlm_answer=vlm_answer)
        else:
            final_answer = self.mistral.generate_answer(question=question, context=caption)
        return final_answer
