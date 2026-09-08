from rest_framework import serializers


class ReportQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    product = serializers.IntegerField(required=False)
    category = serializers.IntegerField(required=False)
    supplier = serializers.IntegerField(required=False)
    user = serializers.IntegerField(required=False)
    movement_type = serializers.ChoiceField(
        choices=('IN', 'OUT', 'ADJUSTMENT'),
        required=False,
    )
    status = serializers.ChoiceField(
        choices=('IN_STOCK', 'LOW_STOCK', 'OUT_OF_STOCK'),
        required=False,
    )

    def validate(self, attrs):
        if attrs.get('start_date') and attrs.get('end_date') \
                and attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError(
                'start_date cannot be after end_date.'
            )
        return attrs
