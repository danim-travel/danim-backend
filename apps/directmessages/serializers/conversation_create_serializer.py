from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.directmessages.models import Conversation
from apps.users.models import User


class ConversationCreateSerializer(serializers.Serializer):
    """
    - 대화방 생성 Request Body 검증 serializer
    - 입력 serializer(사용자로 부터 받아오는 데이터)
    """

    receiver_id = serializers.CharField(max_length=26)


class OpponentSerializer(serializers.Serializer):
    """
    - 중첩 serializer로 출력해줘야하는 데이터 정리
    - S3 DB에 저장된 str그대로 반환할 경우 프론트에서 S3에서 찾을 수 없기에
      user model에 @property를 사용해 url로 변환 후 반환
    """

    user_id = serializers.CharField(source="id")
    nickname = serializers.CharField()
    profile_img = serializers.SerializerMethodField()

    def get_profile_img(self, obj: User) -> str | None:
        return obj.profile_img_url


class ConversationResponseSerializer(serializers.ModelSerializer):
    """
    - 대화방 생성/조회 Response Body 직렬화 serializer(출력)
    - 200(기존 대화방 반환), 201(새 대화방 생성) 공통 사용
    - get_opponent: user1/user2 중 요청한 유저가 누구인지 판별 후 상대방 반환
    """

    conversation_id = serializers.CharField(source="id")
    opponent = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["conversation_id", "opponent", "created_at"]

    @extend_schema_field(OpponentSerializer)
    def get_opponent(self, obj: Conversation) -> dict:
        request_user = self.context["request"].user
        opponent = obj.user2 if obj.user1_id == request_user.id else obj.user1
        return OpponentSerializer(opponent).data
