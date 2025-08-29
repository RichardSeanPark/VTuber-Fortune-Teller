import json
import chardet
from loguru import logger
from pathlib import Path

class Live2dModel:
    """
    A class to represent a Live2D model. This class only prepares and stores the information of the Live2D model.
    Based on reference implementation from open-llm-vtuber project.

    Attributes:
        model_dict_path (str): The path to the model dictionary file.
        live2d_model_name (str): The name of the Live2D model.
        model_info (dict): The information of the Live2D model.
        emo_map (dict): The emotion map of the Live2D model.
        emo_str (str): The string representation of the emotion map of the Live2D model.
    """

    model_dict_path: str
    live2d_model_name: str
    model_info: dict
    emo_map: dict
    emo_str: str

    def __init__(
        self, live2d_model_name: str, model_dict_path: str = "model_dict.json"
    ):
        logger.info(f"[Live2dModel] 초기화 시작: {live2d_model_name}")
        self.model_dict_path: str = model_dict_path
        self.live2d_model_name: str = live2d_model_name
        self.set_model(live2d_model_name)
        logger.info(f"[Live2dModel] 초기화 완료: {live2d_model_name}")

    def set_model(self, model_name: str) -> None:
        """
        Set the model with its name and load the model information.
        This method will initialize the `self.model_info`, `self.emo_map`, and `self.emo_str` attributes.

        Parameters:
            model_name (str): The name of the live2d model.

        Returns:
            None
        """
        logger.info(f"[Live2dModel] 모델 설정 시작: {model_name}")

        self.model_info: dict = self._lookup_model_info(model_name)
        self.emo_map: dict = {
            k.lower(): v for k, v in self.model_info["emotionMap"].items()
        }
        self.emo_str: str = " ".join([f"[{key}]," for key in self.emo_map.keys()])
        
        logger.info(f"[Live2dModel] 감정 맵 로드 완료: {list(self.emo_map.keys())}")
        logger.info(f"[Live2dModel] 감정 문자열: {self.emo_str}")

    def _load_file_content(self, file_path: str) -> str:
        """Load the content of a file with robust encoding handling."""
        logger.debug(f"[Live2dModel] 파일 로드 시도: {file_path}")
        
        # Try common encodings first
        encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "ascii"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as file:
                    content = file.read()
                    logger.debug(f"[Live2dModel] 파일 로드 성공 (인코딩: {encoding})")
                    return content
            except UnicodeDecodeError:
                continue

        # If all common encodings fail, try to detect encoding
        try:
            with open(file_path, "rb") as file:
                raw_data = file.read()
            detected = chardet.detect(raw_data)
            detected_encoding = detected["encoding"]

            if detected_encoding:
                try:
                    content = raw_data.decode(detected_encoding)
                    logger.debug(f"[Live2dModel] 파일 로드 성공 (감지된 인코딩: {detected_encoding})")
                    return content
                except UnicodeDecodeError:
                    pass
        except Exception as e:
            logger.error(f"[Live2dModel] 인코딩 감지 실패 {file_path}: {e}")

        raise UnicodeError(f"Failed to decode {file_path} with any encoding")

    def _lookup_model_info(self, model_name: str) -> dict:
        """
        Find the model information from the model dictionary and return the information about the matched model.

        Parameters:
            model_name (str): The name of the live2d model.

        Returns:
            dict: The dictionary with the information of the matched model.

        Raises:
            FileNotFoundError if the model dictionary file is not found.
            json.JSONDecodeError if the model dictionary file is not a valid JSON file.
            KeyError if the model name is not found in the model dictionary.
        """
        logger.info(f"[Live2dModel] 모델 정보 조회: {model_name}")
        
        self.live2d_model_name = model_name

        try:
            # model_dict.json 파일 경로 확인
            model_dict_path = Path(self.model_dict_path)
            if not model_dict_path.exists():
                # reference 폴더에서 찾기
                reference_path = Path("../../../reference/model_dict.json")
                if reference_path.exists():
                    self.model_dict_path = str(reference_path)
                    logger.info(f"[Live2dModel] reference 폴더에서 model_dict.json 사용: {self.model_dict_path}")
                else:
                    raise FileNotFoundError(f"model_dict.json not found at {self.model_dict_path}")
            
            file_content = self._load_file_content(self.model_dict_path)
            model_dict = json.loads(file_content)
            logger.info(f"[Live2dModel] model_dict.json 로드 성공, 모델 수: {len(model_dict)}")
            
        except FileNotFoundError as file_e:
            logger.critical(f"[Live2dModel] 모델 사전 파일을 찾을 수 없음: {self.model_dict_path}")
            raise file_e
        except json.JSONDecodeError as json_e:
            logger.critical(f"[Live2dModel] JSON 디코딩 실패: {self.model_dict_path}")
            raise json_e
        except UnicodeError as uni_e:
            logger.critical(f"[Live2dModel] 파일 읽기 실패: {self.model_dict_path}")
            raise uni_e
        except Exception as e:
            logger.critical(f"[Live2dModel] 알 수 없는 오류: {self.model_dict_path}")
            raise e

        # Find the model in the model_dict
        matched_model = next(
            (model for model in model_dict if model["name"] == model_name), None
        )

        if matched_model is None:
            available_models = [model["name"] for model in model_dict]
            logger.critical(f"[Live2dModel] 모델 '{model_name}'을 찾을 수 없음. 사용 가능한 모델: {available_models}")
            raise KeyError(
                f"{model_name} not found in model dictionary {self.model_dict_path}."
            )

        logger.info(f"[Live2dModel] 모델 정보 로드 성공: {model_name}")
        logger.debug(f"[Live2dModel] 모델 세부 정보: {matched_model}")

        return matched_model

    def extract_emotion(self, str_to_check: str) -> list:
        """
        Check the input string for any emotion keywords and return a list of values (the expression index) of the emotions found in the string.

        Parameters:
            str_to_check (str): The string to check for emotions.

        Returns:
            list: A list of values of the emotions found in the string. An empty list is returned if no emotions are found.
        """
        logger.debug(f"[Live2dModel] 감정 추출 시작: '{str_to_check[:50]}...'")

        expression_list = []
        str_to_check = str_to_check.lower()

        i = 0
        while i < len(str_to_check):
            if str_to_check[i] != "[":
                i += 1
                continue
            for key in self.emo_map.keys():
                emo_tag = f"[{key}]"
                if str_to_check[i : i + len(emo_tag)] == emo_tag:
                    expression_list.append(self.emo_map[key])
                    logger.debug(f"[Live2dModel] 감정 발견: {key} -> {self.emo_map[key]}")
                    i += len(emo_tag) - 1
                    break
            i += 1
            
        logger.info(f"[Live2dModel] 추출된 감정 인덱스: {expression_list}")
        return expression_list

    def remove_emotion_keywords(self, target_str: str) -> str:
        """
        Remove the emotion keywords from the input string and return the cleaned string.

        Parameters:
            target_str (str): The string to check for emotions.

        Returns:
            str: The cleaned string with the emotion keywords removed.
        """
        logger.debug(f"[Live2dModel] 감정 키워드 제거 시작: '{target_str[:50]}...'")
        
        original_str = target_str
        lower_str = target_str.lower()

        for key in self.emo_map.keys():
            lower_key = f"[{key}]".lower()
            while lower_key in lower_str:
                start_index = lower_str.find(lower_key)
                end_index = start_index + len(lower_key)
                target_str = target_str[:start_index] + target_str[end_index:]
                lower_str = lower_str[:start_index] + lower_str[end_index:]
                
        cleaned_str = target_str.strip()
        if cleaned_str != original_str:
            logger.info(f"[Live2dModel] 감정 키워드 제거 완료")
            logger.debug(f"[Live2dModel] 원본: '{original_str[:50]}...'")
            logger.debug(f"[Live2dModel] 정리됨: '{cleaned_str[:50]}...'")
        
        return cleaned_str

    def get_model_info(self) -> dict:
        """
        Get the model information.

        Returns:
            dict: The model information.
        """
        return self.model_info

    def get_emotion_map(self) -> dict:
        """
        Get the emotion map.

        Returns:
            dict: The emotion map.
        """
        return self.emo_map

    def get_emotion_string(self) -> str:
        """
        Get the emotion string for LLM prompt.

        Returns:
            str: The emotion string.
        """
        return self.emo_str

    def get_available_expressions(self) -> list:
        """
        Get list of available expression names.

        Returns:
            list: List of expression names.
        """
        return list(self.emo_map.keys())

    def get_model_name(self) -> str:
        """
        Get the current model name.

        Returns:
            str: The model name.
        """
        return self.live2d_model_name