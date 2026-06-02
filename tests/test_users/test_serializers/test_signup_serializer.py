from datetime import date

from django.test import TestCase

from apps.users.serializers.signup_serializer import UserSignUpSerializer


class UserSignUpSerializerTest(TestCase):

    def test_signup_serializer(self) -> None:
        """정상 serializer test"""
        serializer = UserSignUpSerializer(
            data={
                "email_token": "abc123",
                "password": "Password@1",
                "password_confirm": "Password@1",
                "nickname": "testnickname",
                "name": "testname",
                "birth_day": date(1970, 1, 1),
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_signup_serializer_password_and_confirm_password_error(self) -> None:
        """비밀번호 및 비밀번호 확인 불일치"""
        serializer = UserSignUpSerializer(
            data={
                "email_token": "abc123",
                "password": "Password@1",
                "password_confirm": "Password@2",
                "nickname": "testnickname",
                "name": "testname",
                "birth_day": date(1970, 1, 1),
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_signup_serializer_password_under(self) -> None:
        """비밀번호 8자리 미만"""
        serializer = UserSignUpSerializer(
            data={
                "email_token": "abc123",
                "password": "Pass@1",
                "password_confirm": "Pass@1",
                "nickname": "testnickname",
                "name": "testname",
                "birth_day": date(1970, 1, 1),
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_signup_serializer_password_without_special_symbol(self) -> None:
        """비밀번호 특수문자 미포함"""
        serializer = UserSignUpSerializer(
            data={
                "email_token": "abc123",
                "password": "Password1",
                "password_confirm": "Password1",
                "nickname": "testnickname",
                "name": "testname",
                "birth_day": date(1970, 1, 1),
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_signup_serializer_password_without_big_word(self) -> None:
        """비밀번호 대문자 미포함"""
        serializer = UserSignUpSerializer(
            data={
                "email_token": "abc123",
                "password": "password@1",
                "password_confirm": "password@1",
                "nickname": "testnickname",
                "name": "testname",
                "birth_day": date(1970, 1, 1),
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_signup_serializer_password_without_number(self) -> None:
        """비밀번호 숫자 미포함"""
        serializer = UserSignUpSerializer(
            data={
                "email_token": "abc123",
                "password": "Password@",
                "password_confirm": "Password@",
                "nickname": "testnickname",
                "name": "testname",
                "birth_day": date(1970, 1, 1),
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_signup_serializer_nickname_invalid_character(self) -> None:
        """닉네임 중복에 관한 테스트"""
        serializer = UserSignUpSerializer(
            data={
                "email_token": "abc123",
                "password": "Password@1",
                "password_confirm": "Password@1",
                "nickname": "테스트닉네임",
                "name": "testname",
                "birth_day": date(1970, 1, 1),
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_signup_serializer_birth_day_future(self) -> None:
        """미래 날짜 생년월일"""
        serializer = UserSignUpSerializer(
            data={
                "email_token": "abc123",
                "password": "Password@1",
                "password_confirm": "Password@1",
                "nickname": "testnickname",
                "name": "testname",
                "birth_day": date(2099, 1, 1),
            }
        )
        self.assertFalse(serializer.is_valid())
