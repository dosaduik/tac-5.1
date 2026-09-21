import pytest
import os
from unittest.mock import patch, MagicMock
from core.llm_processor import (
    generate_random_query_with_openai,
    generate_random_query_with_anthropic,
    generate_random_query,
    truncate_to_two_sentences
)


class TestGenerateRandomQuery:

    @patch('core.llm_processor.OpenAI')
    def test_generate_random_query_with_openai_success(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "What is the average age of users in the users table?"
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            schema_info = {
                'tables': {
                    'users': {
                        'columns': {'id': 'INTEGER', 'name': 'TEXT', 'age': 'INTEGER'},
                        'row_count': 100
                    }
                }
            }

            result = generate_random_query_with_openai(schema_info)

            assert result == "What is the average age of users in the users table?"
            mock_client.chat.completions.create.assert_called_once()

            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]['model'] == 'gpt-4.1-mini'
            assert call_args[1]['temperature'] == 0.7
            assert call_args[1]['max_tokens'] == 500

    @patch('core.llm_processor.OpenAI')
    def test_generate_random_query_with_openai_clean_markdown(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```\nWhich products have the highest price?\n```"
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            schema_info = {'tables': {'products': {'columns': {'price': 'REAL'}, 'row_count': 10}}}

            result = generate_random_query_with_openai(schema_info)

            assert result == "Which products have the highest price?"

    def test_generate_random_query_with_openai_no_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            schema_info = {'tables': {}}

            with pytest.raises(Exception) as exc_info:
                generate_random_query_with_openai(schema_info)

            assert "OPENAI_API_KEY environment variable not set" in str(exc_info.value)

    @patch('core.llm_processor.OpenAI')
    def test_generate_random_query_with_openai_api_error(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            schema_info = {'tables': {}}

            with pytest.raises(Exception) as exc_info:
                generate_random_query_with_openai(schema_info)

            assert "Error generating random query with OpenAI" in str(exc_info.value)

    @patch('core.llm_processor.Anthropic')
    def test_generate_random_query_with_anthropic_success(self, mock_anthropic_class):
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content[0].text = "Which orders were placed in the last month?"
        mock_client.messages.create.return_value = mock_response

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            schema_info = {
                'tables': {
                    'orders': {
                        'columns': {'id': 'INTEGER', 'created_at': 'TEXT'},
                        'row_count': 50
                    }
                }
            }

            result = generate_random_query_with_anthropic(schema_info)

            assert result == "Which orders were placed in the last month?"
            mock_client.messages.create.assert_called_once()

            call_args = mock_client.messages.create.call_args
            assert call_args[1]['model'] == 'claude-haiku-4-5'
            assert call_args[1]['temperature'] == 0.7
            assert call_args[1]['max_tokens'] == 500

    @patch('core.llm_processor.Anthropic')
    def test_generate_random_query_with_anthropic_clean_markdown(self, mock_anthropic_class):
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content[0].text = "```\nHow many events happened last week?\n```"
        mock_client.messages.create.return_value = mock_response

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            schema_info = {'tables': {'events': {'columns': {'ts': 'TEXT'}, 'row_count': 5}}}

            result = generate_random_query_with_anthropic(schema_info)

            assert result == "How many events happened last week?"

    def test_generate_random_query_with_anthropic_no_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            schema_info = {'tables': {}}

            with pytest.raises(Exception) as exc_info:
                generate_random_query_with_anthropic(schema_info)

            assert "ANTHROPIC_API_KEY environment variable not set" in str(exc_info.value)

    @patch('core.llm_processor.Anthropic')
    def test_generate_random_query_with_anthropic_api_error(self, mock_anthropic_class):
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            schema_info = {'tables': {}}

            with pytest.raises(Exception) as exc_info:
                generate_random_query_with_anthropic(schema_info)

            assert "Error generating random query with Anthropic" in str(exc_info.value)

    def test_truncate_to_two_sentences_truncates_long_text(self):
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."

        result = truncate_to_two_sentences(text)

        assert result == "First sentence. Second sentence."

    def test_truncate_to_two_sentences_leaves_one_sentence_unchanged(self):
        text = "Just one sentence."

        result = truncate_to_two_sentences(text)

        assert result == "Just one sentence."

    def test_truncate_to_two_sentences_leaves_two_sentences_unchanged(self):
        text = "First sentence. Second sentence."

        result = truncate_to_two_sentences(text)

        assert result == "First sentence. Second sentence."

    def test_truncate_to_two_sentences_no_terminal_punctuation(self):
        text = "This has no terminal punctuation"

        result = truncate_to_two_sentences(text)

        assert result == text

    @patch('core.llm_processor.generate_random_query_with_openai')
    def test_generate_random_query_openai_key_priority(self, mock_openai_func):
        mock_openai_func.return_value = "What is the total revenue?"

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key', 'ANTHROPIC_API_KEY': 'anthropic-key'}):
            schema_info = {'tables': {'orders': {'columns': {}, 'row_count': 1}}}

            result = generate_random_query(schema_info, llm_provider="anthropic")

            assert result == "What is the total revenue?"
            mock_openai_func.assert_called_once_with(schema_info)

    @patch('core.llm_processor.generate_random_query_with_anthropic')
    def test_generate_random_query_anthropic_fallback(self, mock_anthropic_func):
        mock_anthropic_func.return_value = "How many users signed up this year?"

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'anthropic-key'}, clear=True):
            schema_info = {'tables': {'users': {'columns': {}, 'row_count': 1}}}

            result = generate_random_query(schema_info, llm_provider="openai")

            assert result == "How many users signed up this year?"
            mock_anthropic_func.assert_called_once_with(schema_info)

    @patch('core.llm_processor.generate_random_query_with_openai')
    def test_generate_random_query_request_preference_openai(self, mock_openai_func):
        mock_openai_func.return_value = "What is the most common product category?"

        with patch.dict(os.environ, {}, clear=True):
            schema_info = {'tables': {'products': {'columns': {}, 'row_count': 1}}}

            result = generate_random_query(schema_info, llm_provider="openai")

            assert result == "What is the most common product category?"
            mock_openai_func.assert_called_once_with(schema_info)

    @patch('core.llm_processor.generate_random_query_with_anthropic')
    def test_generate_random_query_request_preference_anthropic(self, mock_anthropic_func):
        mock_anthropic_func.return_value = "Which customers ordered the most?"

        with patch.dict(os.environ, {}, clear=True):
            schema_info = {'tables': {'customers': {'columns': {}, 'row_count': 1}}}

            result = generate_random_query(schema_info, llm_provider="anthropic")

            assert result == "Which customers ordered the most?"
            mock_anthropic_func.assert_called_once_with(schema_info)

    def test_generate_random_query_no_tables_raises(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key'}):
            schema_info = {'tables': {}}

            with pytest.raises(Exception) as exc_info:
                generate_random_query(schema_info)

            assert "No tables available" in str(exc_info.value)
