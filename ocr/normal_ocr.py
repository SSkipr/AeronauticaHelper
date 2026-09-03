'''
      .o.                                    ooooo   ooooo           oooo
     .888.                                   888'   888'           888
    .8"888.      .ooooo.  oooo d8b  .ooooo.   888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b
   .8' 888.    d88' 88b 888""8P d88' 88b  888ooooo888  d88' 88b  888   888' 88b d88' 88b 888""8P
  .88ooo8888.   888ooo888  888     888   888  888     888  888ooo888  888   888   888 888ooo888  888
 .8'     888.  888    .o  888     888   888  888     888  888    .o  888   888   888 888    .o  888
o.oooooo..o88.oooooo..oPoooo88b    Yo8od8P' o888o   o888o Y8bod8P' o888o  888bod8P' Y8bod8P' d888b
d8P'    Y8 d8P'    Y8 888         "'                                    888
Y88bo.      Y88bo.       888  oooo  oooo  oo.ooooo.  oooo d8b              o888o
 "Y8888o.   "Y8888o.   888 .8P'   888   888' 88b 888""8P
     "Y88b      "Y88b  888888.     888   888   888  888
oo     .d8P oo     .d8P  888 `88b.   888   888   888  888
8""88888P'  8""88888P'  o888o o888o o888o  888bod8P' d888b
                                           888
                                          o888o

https://aeronautica-helper.vercel.app
https://github.com/SSkipr/AeronauticaHelper
Version 4.1.4
'''

import asyncio
import re
import os
import tempfile
import threading
import time
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    try:
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    except AttributeError:
        Image.ANTIALIAS = getattr(Image, 'LANCZOS', 1)
from AeroHelper.utils.platform import IS_WINDOWS, IS_MACOS
_WINSDK_AVAILABLE = False
_CLICK_MIN_CONFIDENCE = 0.45
OcrEngine = None
Language = None
BitmapDecoder = None
InMemoryRandomAccessStream = None
DataWriter = None
StorageFile = None
if IS_WINDOWS:
    try:
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.globalization import Language
        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter
        from winsdk.windows.storage import StorageFile
        _WINSDK_AVAILABLE = True
    except Exception:
        _WINSDK_AVAILABLE = False
_VISION_AVAILABLE = False
if IS_MACOS:
    try:
        import Vision
        import Quartz
        _VISION_AVAILABLE = True
    except Exception:
        _VISION_AVAILABLE = False

class NormalOCR:

    def __init__(self, logger=None, ocr_debug_mode=False):
        self.logger = logger
        self._ocr_debug_mode_override = bool(ocr_debug_mode)
        self.easyocr_reader = None
        self.easyocr_available = False
        self.last_confidence = None
        self.last_region_count = 0
        self.last_high_confidence_count = 0
        self.preferred_icao_code = None
        self.prefer_custom_waypoint = False
        self._windows_loop = None
        self._windows_loop_thread = None
        self._init_easyocr()

    @property
    def ocr_debug_mode(self):
        if self.logger is not None and getattr(self.logger, 'ocr_debug_enabled', False):
            return True
        return bool(getattr(self, '_ocr_debug_mode_override', False))

    def _log(self, level, message):
        if self.logger:
            if level == 'debug':
                self.logger.debug(message)
            elif level == 'info':
                self.logger.info(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)

    def _log_ocr_bundle(self, context, image_path, sections):
        if not self.ocr_debug_mode:
            return
        path = os.path.basename(str(image_path or '')) or '?'
        parts = [f'[OCR] {context} image={path}']
        for name, text in sections.items():
            t = text if text is not None else ''
            parts.append(f'--- {name} ({len(t)} chars) ---')
            parts.append(t)
        self._log('debug', '\n'.join(parts))

    def _easyocr_reader_kwargs(self):
        import sys
        from pathlib import Path
        kwargs = {'gpu': False}
        if getattr(sys, 'frozen', False):
            model_dir = Path(getattr(sys, '_MEIPASS', '')) / 'easyocr_models'
            if model_dir.is_dir():
                kwargs['model_storage_directory'] = str(model_dir)
                kwargs['download_enabled'] = False
        return kwargs

    def _init_easyocr(self):
        try:
            import easyocr
            self._log('info', 'Initializing EasyOCR engine...')
            self.easyocr_reader = easyocr.Reader(['en'], **self._easyocr_reader_kwargs())
            self.easyocr_available = True
            if IS_WINDOWS and _WINSDK_AVAILABLE:
                self._log('info', 'EasyOCR ready (dual-engine with Windows OCR)')
            elif IS_MACOS and _VISION_AVAILABLE:
                self._log('info', 'EasyOCR ready (dual-engine with Apple Vision OCR)')
            else:
                self._log('info', 'EasyOCR engine initialized successfully')
        except Exception as e:
            import traceback
            self.easyocr_reader = None
            self.easyocr_available = False
            self._log('warning', f'EasyOCR initialization failed: {str(e)}')
            if self.logger:
                self.logger.error_detailed('EasyOCR initialization failed', f'Exception: {str(e)}\n{traceback.format_exc()}')

    def _easyocr_extract(self, image_path, return_boxes=False):
        if not self.easyocr_available or self.easyocr_reader is None:
            self._log('debug', 'EasyOCR: Not available, skipping')
            return '' if not return_boxes else ([], '')
        if not os.path.exists(image_path):
            self._log('error', f'EasyOCR: Image file does not exist: {image_path}')
            return '' if not return_boxes else ([], '')
        try:
            self._log('debug', f'EasyOCR: Processing image: {image_path} (size: {os.path.getsize(image_path)} bytes)')
            t0 = time.perf_counter()
            results = self.easyocr_reader.readtext(image_path)
            elapsed = time.perf_counter() - t0
            text_parts = []
            total_confidence = 0.0
            high_confidence_count = 0
            boxes_with_text = []
            for result in results:
                if len(result) >= 2:
                    text = result[1]
                    text_parts.append(text)
                    if return_boxes and len(result) >= 3:
                        boxes_with_text.append({'box': result[0], 'text': text, 'confidence': result[2]})
                    if len(result) > 2:
                        confidence = result[2]
                        total_confidence += confidence
                        if confidence > 0.8:
                            high_confidence_count += 1
            text = ' '.join(text_parts)
            avg_confidence = total_confidence / len(results) if results else 0.0
            self.last_confidence = avg_confidence if results else None
            self.last_region_count = len(results)
            self.last_high_confidence_count = high_confidence_count
            self._log('debug', f'EasyOCR: {elapsed:.2f}s, {len(text)} chars, {len(results)} regions')
            if return_boxes:
                return (boxes_with_text, text)
            return text
        except Exception as e:
            import traceback
            self.last_confidence = None
            self.last_region_count = 0
            self.last_high_confidence_count = 0
            self._log('error', f'EasyOCR: Extraction failed: {str(e)}')
            if self.logger:
                self.logger.error_detailed('EasyOCR extraction error', f'Exception: {str(e)}\n{traceback.format_exc()}')
            return '' if not return_boxes else ([], '')

    def _vision_ocr_extract(self, image_path):
        if not _VISION_AVAILABLE:
            return ''
        try:
            if not os.path.exists(image_path):
                self._log('error', f'Vision OCR: Image file does not exist: {image_path}')
                return ''
            import Vision
            import Quartz
            from Foundation import NSURL
            self._log('debug', f'Vision OCR: Processing image: {image_path}')
            t0 = time.perf_counter()
            url = NSURL.fileURLWithPath_(image_path)
            image_source = Quartz.CGImageSourceCreateWithURL(url, None)
            if image_source is None:
                self._log('error', 'Vision OCR: Failed to create CGImageSource')
                return ''
            cg_image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
            if cg_image is None:
                self._log('error', 'Vision OCR: Failed to create CGImage')
                return ''
            request = Vision.VNRecognizeTextRequest.alloc().init()
            try:
                request.setRecognitionLevel_(1)
            except Exception:
                pass
            try:
                request.setUsesLanguageCorrection_(True)
            except Exception:
                pass
            handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
            ok, err = handler.performRequests_error_([request], None)
            if not ok:
                err_msg = str(err) if err is not None else 'unknown error'
                self._log('warning', f'Vision OCR: performRequests failed: {err_msg}')
                return ''
            text_parts = []
            results = request.results() or []
            for obs in results:
                try:
                    top_candidates = obs.topCandidates_(1)
                    if top_candidates and len(top_candidates) > 0:
                        text_parts.append(str(top_candidates[0].string()))
                except Exception:
                    continue
            combined = ' '.join(text_parts).strip()
            elapsed = time.perf_counter() - t0
            self._log('debug', f'Vision OCR: {elapsed:.2f}s, {len(combined)} chars, {len(results)} regions')
            return combined
        except Exception as e:
            import traceback
            self._log('error', f'Vision OCR: Extraction failed: {e}')
            if self.logger:
                self.logger.error_detailed('Vision OCR extraction error', f'Exception: {e}\n{traceback.format_exc()}')
            return ''

    def _vision_normalized_box_to_pixels(self, bbox, img_w, img_h):
        x = float(bbox.origin.x) * img_w
        w = float(bbox.size.width) * img_w
        h = float(bbox.size.height) * img_h
        y = (1.0 - float(bbox.origin.y) - float(bbox.size.height)) * img_h
        return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]

    def _vision_ocr_word_boxes(self, image_path):
        if not _VISION_AVAILABLE:
            return []
        try:
            if not os.path.exists(image_path):
                self._log('error', f'Vision OCR: Image file does not exist: {image_path}')
                return []
            import Vision
            import Quartz
            from Foundation import NSURL
            url = NSURL.fileURLWithPath_(image_path)
            image_source = Quartz.CGImageSourceCreateWithURL(url, None)
            if image_source is None:
                return []
            cg_image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
            if cg_image is None:
                return []
            img_w = Quartz.CGImageGetWidth(cg_image)
            img_h = Quartz.CGImageGetHeight(cg_image)
            request = Vision.VNRecognizeTextRequest.alloc().init()
            try:
                request.setRecognitionLevel_(1)
            except Exception:
                pass
            handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
            ok, err = handler.performRequests_error_([request], None)
            if not ok:
                err_msg = str(err) if err is not None else 'unknown error'
                self._log('warning', f'Vision OCR: performRequests failed: {err_msg}')
                return []
            words = []
            for obs in request.results() or []:
                try:
                    top_candidates = obs.topCandidates_(1)
                    if not top_candidates or len(top_candidates) == 0:
                        continue
                    candidate = top_candidates[0]
                    text = str(candidate.string())
                    try:
                        confidence = float(candidate.confidence())
                    except Exception:
                        confidence = 1.0
                    box = self._vision_normalized_box_to_pixels(obs.boundingBox(), img_w, img_h)
                    x_coords = [point[0] for point in box]
                    y_coords = [point[1] for point in box]
                    center_x = int(sum(x_coords) / len(x_coords))
                    center_y = int(sum(y_coords) / len(y_coords))
                    words.append({
                        'box': box,
                        'text': text,
                        'confidence': confidence,
                        'center': (center_x, center_y),
                    })
                except Exception:
                    continue
            return words
        except Exception as e:
            import traceback
            self._log('error', f'Vision OCR: Word box extraction failed: {e}')
            if self.logger:
                self.logger.error_detailed('Vision OCR word box error', f'Exception: {e}\n{traceback.format_exc()}')
            return []

    def _vision_ocr_find_boxes(self, image_path, target_text, match_mode='contains'):
        words = self._vision_ocr_word_boxes(image_path)
        matches = self._merge_word_phrase_matches(words, target_text, match_mode)
        if matches:
            self._log('info', f'find_text_boxes: Found {len(matches)} matches for "{target_text}" (mode={match_mode}) via Vision OCR')
        elif self.ocr_debug_mode:
            native_text = ' '.join(entry['text'] for entry in words).strip()
            self._log_ocr_bundle(
                'find_text_boxes',
                image_path,
                {
                    'native_words': native_text,
                    'target': target_text,
                    'match_mode': match_mode,
                    'matches': '0',
                },
            )
        return matches

    async def _windows_ocr_extract_async(self, image_path):
        if not _WINSDK_AVAILABLE:
            return ''
        try:
            if not os.path.exists(image_path):
                self._log('error', f'Windows OCR: Image file does not exist: {image_path}')
                return ''
            file_size = os.path.getsize(image_path)
            self._log('debug', f'Windows OCR: Processing image: {image_path} (size: {file_size} bytes)')
            t0 = time.perf_counter()
            try:
                storage_file = await StorageFile.get_file_from_path_async(image_path)
                self._log('debug', 'Windows OCR: Got storage file from path')
                file_stream = await storage_file.open_read_async()
                self._log('debug', 'Windows OCR: Opened file stream for reading')
                decoder = await BitmapDecoder.create_async(file_stream)
                bitmap = await decoder.get_software_bitmap_async()
                self._log('debug', 'Windows OCR: Decoded bitmap')
                file_stream.close()
            except Exception as file_error:
                self._log('warning', f'Windows OCR: File-based approach failed ({file_error}), trying memory stream approach')
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                self._log('debug', f'Windows OCR: Loaded {len(image_data)} bytes from file')
                stream = InMemoryRandomAccessStream()
                data_writer = DataWriter(stream)
                self._write_winrt_bytes(data_writer, image_data)
                await data_writer.store_async()
                await data_writer.flush_async()
                stream.seek(0)
                self._log('debug', 'Windows OCR: Created memory stream with DataWriter')
                decoder = await BitmapDecoder.create_async(stream)
                bitmap = await decoder.get_software_bitmap_async()
                self._log('debug', 'Windows OCR: Decoded bitmap from memory stream')
            engine = OcrEngine.try_create_from_user_profile_languages()
            if engine is None:
                self._log('debug', 'Windows OCR: Trying to create engine with English language')
                engine = OcrEngine.try_create_from_language(Language('en'))
            if engine is None:
                self._log('error', 'Windows OCR: Failed to create OCR engine')
                return ''
            self._log('debug', 'Windows OCR: Engine created successfully')
            result = await engine.recognize_async(bitmap)
            self._log('debug', f'Windows OCR: Recognition completed, found {len(result.lines)} lines')
            text_parts = []
            for line in result.lines:
                line_text = ''
                for word in line.words:
                    line_text += word.text + ' '
                text_parts.append(line_text.strip())
            combined_text = ' '.join(text_parts)
            elapsed = time.perf_counter() - t0
            self._log('debug', f'Windows OCR: {elapsed:.2f}s, {len(combined_text)} chars, {len(result.lines)} lines')
            return combined_text
        except Exception as e:
            import traceback
            self._log('error', f'Windows OCR: Extraction failed: {str(e)}')
            if self.logger:
                self.logger.error_detailed('Windows OCR extraction error', f'Exception: {str(e)}\n{traceback.format_exc()}')
            return ''

    def _ensure_windows_loop(self):
        loop = getattr(self, '_windows_loop', None)
        thread = getattr(self, '_windows_loop_thread', None)
        if loop is not None and not loop.is_closed() and thread is not None and thread.is_alive():
            return loop
        ready = threading.Event()
        holder = {}

        def runner():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            holder['loop'] = new_loop
            self._windows_loop = new_loop
            ready.set()
            new_loop.run_forever()

        thread = threading.Thread(target=runner, name='AeroHelperWinRTOCR', daemon=True)
        self._windows_loop_thread = thread
        thread.start()
        if not ready.wait(timeout=5):
            raise RuntimeError('Windows OCR event loop failed to start')
        return holder['loop']

    def _run_windows_coro(self, factory):
        loop = self._ensure_windows_loop()
        future = asyncio.run_coroutine_threadsafe(factory(), loop)
        return future.result(timeout=45)

    def _write_winrt_bytes(self, data_writer, image_data):
        chunk = 65536
        for offset in range(0, len(image_data), chunk):
            data_writer.write_bytes(list(image_data[offset:offset + chunk]))

    def _windows_ocr_extract(self, image_path):
        if not _WINSDK_AVAILABLE:
            return ''
        try:
            self._log('debug', 'Windows OCR: Starting async extraction')
            return self._run_windows_coro(lambda: self._windows_ocr_extract_async(image_path))
        except Exception as e:
            import traceback
            self._log('error', f'Windows OCR: Async wrapper failed: {str(e)}')
            if self.logger:
                self.logger.error_detailed('Windows OCR async wrapper error', f'Exception: {str(e)}\n{traceback.format_exc()}')
            return ''

    def _rect_to_box(self, rect):
        x = float(rect.x)
        y = float(rect.y)
        w = float(rect.width)
        h = float(rect.height)
        return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]

    def _word_entry_from_winrt(self, word, confidence=1.0):
        box = self._rect_to_box(word.bounding_rect)
        x_coords = [point[0] for point in box]
        y_coords = [point[1] for point in box]
        center_x = int(sum(x_coords) / len(x_coords))
        center_y = int(sum(y_coords) / len(y_coords))
        return {
            'box': box,
            'text': word.text,
            'confidence': confidence,
            'center': (center_x, center_y),
        }

    async def _windows_ocr_load_bitmap_async(self, image_path):
        try:
            storage_file = await StorageFile.get_file_from_path_async(image_path)
            file_stream = await storage_file.open_read_async()
            decoder = await BitmapDecoder.create_async(file_stream)
            bitmap = await decoder.get_software_bitmap_async()
            file_stream.close()
            return bitmap
        except Exception as file_error:
            self._log('warning', f'Windows OCR: File-based load failed ({file_error}), trying memory stream')
            with open(image_path, 'rb') as f:
                image_data = f.read()
            stream = InMemoryRandomAccessStream()
            data_writer = DataWriter(stream)
            self._write_winrt_bytes(data_writer, image_data)
            await data_writer.store_async()
            await data_writer.flush_async()
            stream.seek(0)
            decoder = await BitmapDecoder.create_async(stream)
            return await decoder.get_software_bitmap_async()

    async def _windows_ocr_words_async(self, image_path):
        if not _WINSDK_AVAILABLE:
            return []
        if not os.path.exists(image_path):
            self._log('error', f'Windows OCR: Image file does not exist: {image_path}')
            return []
        bitmap = await self._windows_ocr_load_bitmap_async(image_path)
        engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            engine = OcrEngine.try_create_from_language(Language('en'))
        if engine is None:
            self._log('error', 'Windows OCR: Failed to create OCR engine')
            return []
        result = await engine.recognize_async(bitmap)
        words = []
        for line in result.lines:
            for word in line.words:
                words.append(self._word_entry_from_winrt(word))
        return words

    def _windows_ocr_word_boxes(self, image_path):
        if not _WINSDK_AVAILABLE:
            return []
        try:
            words = self._run_windows_coro(lambda: self._windows_ocr_words_async(image_path))
            return words
        except Exception as e:
            import traceback
            self._log('error', f'Windows OCR: Word box extraction failed: {str(e)}')
            if self.logger:
                self.logger.error_detailed('Windows OCR word box error', f'Exception: {str(e)}\n{traceback.format_exc()}')
            return []

    def _merge_word_phrase_matches(self, words, target_text, match_mode='contains'):
        matches = []
        for entry in words:
            if self._text_matches(entry['text'], target_text, match_mode):
                matches.append(entry)
        target_parts = [part for part in target_text.strip().split() if part]
        if len(target_parts) < 2 or not words:
            return matches
        ordered = sorted(words, key=lambda entry: (entry['center'][1], entry['center'][0]))
        n = len(target_parts)
        for i in range(len(ordered) - n + 1):
            window = ordered[i:i + n]
            joined = ' '.join(entry['text'] for entry in window)
            if not self._text_matches(joined, target_text, match_mode):
                continue
            xs = [point[0] for entry in window for point in entry['box']]
            ys = [point[1] for entry in window for point in entry['box']]
            box = [[min(xs), min(ys)], [max(xs), min(ys)], [max(xs), max(ys)], [min(xs), max(ys)]]
            center = (int((min(xs) + max(xs)) / 2), int((min(ys) + max(ys)) / 2))
            matches.append({
                'box': box,
                'text': joined,
                'confidence': min(entry.get('confidence', 1.0) for entry in window),
                'center': center,
            })
        return matches

    def _windows_ocr_find_boxes(self, image_path, target_text, match_mode='contains'):
        words = self._windows_ocr_word_boxes(image_path)
        matches = self._merge_word_phrase_matches(words, target_text, match_mode)
        if matches:
            self._log('info', f'find_text_boxes: Found {len(matches)} matches for "{target_text}" (mode={match_mode}) via Windows OCR')
        elif self.ocr_debug_mode:
            native_text = ' '.join(entry['text'] for entry in words).strip()
            self._log_ocr_bundle(
                'find_text_boxes',
                image_path,
                {
                    'native_words': native_text,
                    'target': target_text,
                    'match_mode': match_mode,
                    'matches': '0',
                },
            )
        return matches

    def _native_ocr_extract(self, image_path):
        if _WINSDK_AVAILABLE:
            return self._windows_ocr_extract(image_path)
        if _VISION_AVAILABLE:
            return self._vision_ocr_extract(image_path)
        return ''

    def _create_roi_image(self, image_path, width_frac=0.35, height_frac=0.45):
        try:
            img = Image.open(image_path).convert('RGB')
            w, h = img.size
            crop_w = int(w * width_frac)
            crop_h = int(h * height_frac)
            box = (0, h - crop_h, crop_w, h)
            roi = img.crop(box)
            fd, path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            roi.save(path)
            return path
        except Exception as e:
            self._log('warning', f'ROI crop failed: {e}')
            return None

    def _extract_icao_bearing_quick(self, text):
        icao, bearing = (None, None)
        try:
            from AeroHelper.utils.icao import extract_icao_and_bearing
            preferred = getattr(self, 'preferred_icao_code', None)
            prefer_custom = bool(getattr(self, 'prefer_custom_waypoint', False))
            icao, bearing = extract_icao_and_bearing(text, preferred_code=preferred, prefer_custom=prefer_custom)
        except Exception:
            pass
        return (icao, bearing)

    def _preferred_already_resolved(self, combined_text):
        preferred = (getattr(self, 'preferred_icao_code', None) or '').upper().strip()
        if not preferred:
            return False
        try:
            from AeroHelper.utils.icao import is_junk_icao_token
            if is_junk_icao_token(preferred):
                return False
        except Exception:
            pass
        icao, bearing = self._extract_icao_bearing_quick(combined_text)
        return icao is not None and icao.upper() == preferred and bearing is not None

    def _needs_roi_icao_fallback(self, combined_text):
        if self._preferred_already_resolved(combined_text):
            return False
        icao, bearing = self._extract_icao_bearing_quick(combined_text)
        try:
            from AeroHelper.utils.icao import is_icao_match_suspicious
            return is_icao_match_suspicious(icao, bearing, combined_text)
        except Exception:
            return icao is None or bearing is None

    def _merge_roi_text_if_needed(self, image_path, combined_text):
        if not self._needs_roi_icao_fallback(combined_text) or not os.path.exists(image_path):
            return combined_text
        roi_path = self._create_roi_image(image_path)
        if not roi_path:
            return combined_text
        try:
            self._log('debug', 'OCR: DEST/bearing missing or suspicious, trying ROI fallback (minimap crop)')
            roi_easy = self._easyocr_extract(roi_path)
            roi_native = self._native_ocr_extract(roi_path)
            roi_text = f'{roi_native} {roi_easy}'.strip()
            if roi_text:
                if self.ocr_debug_mode:
                    self._log_ocr_bundle(
                        'roi_fallback',
                        roi_path,
                        {
                            'native': roi_native or '',
                            'easyocr': roi_easy or '',
                            'merged': roi_text,
                        },
                    )
                else:
                    self._log('info', 'OCR: Merged ROI text for DEST/bearing')
                return f'{combined_text} {roi_text}'.strip()
            return combined_text
        finally:
            if os.path.exists(roi_path):
                os.unlink(roi_path)

    def extract_text(self, image_path, return_boxes=False):
        native_text = self._native_ocr_extract(image_path)
        easyocr_result = self._easyocr_extract(image_path, return_boxes=return_boxes)
        easyocr_boxes, easyocr_text = easyocr_result if return_boxes else (None, easyocr_result)
        combined_text = f'{native_text} {easyocr_text}'.strip()
        combined_text = self._merge_roi_text_if_needed(image_path, combined_text)
        if not combined_text:
            self._log('warning', 'OCR: No text extracted from any engine!')
        engine_name = 'winrt' if _WINSDK_AVAILABLE else ('vision' if _VISION_AVAILABLE else 'native')
        if self.logger:
            self.logger.capture_ocr(
                combined_text,
                source='extract_text',
                sections={
                    engine_name: native_text or '',
                    'easyocr': easyocr_text or '',
                    'combined': combined_text or '',
                },
                image_path=image_path,
            )
        if return_boxes:
            return (easyocr_boxes, combined_text)
        return combined_text

    def _easyocr_find_boxes(self, image_path, target_text, match_mode='contains'):
        if not (self.easyocr_available and self.easyocr_reader is not None):
            return []
        try:
            results = self.easyocr_reader.readtext(image_path)
            matches = []
            scanned_parts = []
            target_lower = target_text.lower()
            for result in results:
                if len(result) >= 3:
                    box = result[0]
                    text = result[1]
                    confidence = result[2]
                    scanned_parts.append(text)
                    text_lower = text.lower().strip()
                    matched = False
                    if match_mode == 'contains':
                        matched = target_lower in text_lower
                    elif match_mode == 'word':
                        matched = bool(re.search('\\b' + re.escape(target_lower) + '\\b', text_lower))
                    elif match_mode == 'startswith':
                        matched = text_lower.startswith(target_lower)
                    elif match_mode == 'exact':
                        matched = text_lower == target_lower
                    if matched:
                        try:
                            if confidence is not None and float(confidence) < _CLICK_MIN_CONFIDENCE:
                                continue
                        except (TypeError, ValueError):
                            pass
                        x_coords = [point[0] for point in box]
                        y_coords = [point[1] for point in box]
                        center_x = int(sum(x_coords) / len(x_coords))
                        center_y = int(sum(y_coords) / len(y_coords))
                        matches.append({'box': box, 'text': text, 'confidence': confidence, 'center': (center_x, center_y)})
            if matches:
                self._log('info', f'find_text_boxes: Found {len(matches)} matches for "{target_text}" (mode={match_mode}) via EasyOCR')
                return matches
            if self.ocr_debug_mode:
                self._log_ocr_bundle(
                    'find_text_boxes',
                    image_path,
                    {
                        'easyocr_scan': ' '.join(scanned_parts),
                        'target': target_text,
                        'match_mode': match_mode,
                        'matches': '0',
                    },
                )
        except Exception as e:
            self._log('error', f'find_text_boxes EasyOCR failed: {str(e)}')
        return []

    def find_text_boxes(self, image_path, target_text, match_mode='contains', prefer_windows=False, allow_easyocr=True):

        if prefer_windows and _WINSDK_AVAILABLE:
            matches = self._windows_ocr_find_boxes(image_path, target_text, match_mode)
            if matches:
                return matches
            if not allow_easyocr:
                return []
        if allow_easyocr:
            matches = self._easyocr_find_boxes(image_path, target_text, match_mode)
            if matches:
                return matches
        if not prefer_windows and _WINSDK_AVAILABLE:
            return self._windows_ocr_find_boxes(image_path, target_text, match_mode)
        if _VISION_AVAILABLE:
            return self._vision_ocr_find_boxes(image_path, target_text, match_mode)
        native_text = self._native_ocr_extract(image_path)
        if self.ocr_debug_mode:
            self._log_ocr_bundle(
                'find_text_boxes',
                image_path,
                {
                    'native': native_text or '',
                    'target': target_text,
                    'match_mode': match_mode,
                },
            )
        if self._text_matches(native_text, target_text, match_mode):
            self._log('info', f'find_text_boxes: Target "{target_text}" found in native OCR but no boxes available')
        return []

    def _text_matches(self, text, target_text, match_mode):
        if not text:
            return False
        target_lower = target_text.lower()
        text_lower = text.lower()
        if match_mode == 'contains':
            return target_lower in text_lower
        if match_mode == 'word':
            return bool(re.search('\\b' + re.escape(target_lower) + '\\b', text_lower))
        if match_mode == 'startswith':
            return text_lower.startswith(target_lower)
        if match_mode == 'exact':
            return text_lower.strip() == target_lower
        return False

    def extract_wp_money(self, text):
        wp = None
        money = None
        money_match = re.search('(\\d[\\d,]*)\\s*Money', text, re.IGNORECASE)
        if money_match:
            money_str = money_match.group(1).replace(',', '')
            try:
                money = int(money_str)
            except ValueError:
                pass
        wp_match = re.search('(\\d[\\d,]*)\\s*WP', text, re.IGNORECASE)
        if wp_match:
            wp_str = wp_match.group(1).replace(',', '')
            try:
                wp = int(wp_str)
            except ValueError:
                pass
        return (wp, money)

    def detect_return_to_lobby(self, text):
        return 'return to lobby' in text.lower()

    def detect_abandon_job(self, text):
        if not text:
            return False
        return bool(re.search(r'abandon\s+job', text, re.IGNORECASE))

    def detect_active_mission(self, text):
        if not text:
            return False
        tl = text.lower()
        if self.detect_abandon_job(text):
            return True
        if re.search(r'end\s+sail', tl) and ('altitude' in tl or 'throttle' in tl or 'controls' in tl):
            return True
        if 'altitude' in tl and 'throttle' in tl and ('hdg' in tl or 'dest' in tl or 'nd/hsi' in tl):
            return True
        if 'transport to' in tl and re.search(r'end\s+sail', tl):
            return True
        return False

    def detect_disconnected(self, text):
        text_lower = text.lower()
        return 'disconnected' in text_lower and 'reconnect' in text_lower
