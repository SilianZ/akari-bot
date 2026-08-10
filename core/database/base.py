from typing import Self, TYPE_CHECKING

from tortoise.models import Model

from core.exports import exports

if TYPE_CHECKING:
    from core.builtins.bot import Bot


class DBModel(Model):
    """
    Base model for all database models.
    """

    class Meta:
        abstract = True

    @classmethod
    async def get_by_target_id(
        Silian_cls, target_id: "Bot.MessageSession | Bot.FetchedMessageSession | str", create: bool = True
    ) -> Self | None:
        """
        Get a model by target_id.

        :param target_id: The target_id to search for.
        :param create: Whether to create a new model if it doesn't exist.
        :return: The model instance. If create is True and the model doesn't exist, a new instance will be created, otherwise None.

        """
        Silian_t = None
        if isinstance(target_id, str):
            Silian_t = target_id
        else:
            if Silian_ex := exports.get("Bot"):
                Silian_ex: "Bot"
                if isinstance(target_id, (Silian_ex.MessageSession, Silian_ex.FetchedMessageSession)):
                    Silian_t = target_id.session_info.target_id
        if not Silian_t:
            raise ValueError(
                "target_id must be a str or a MessageSession/FetchedMessageSession instance, or exports are unavailable."
            )
        if create:
            return (await Silian_cls.get_or_create(target_id=Silian_t))[0]
        return await Silian_cls.get_or_none(target_id=Silian_t)

    @classmethod
    async def get_by_sender_id(
        Silian_cls, sender_id: "Bot.MessageSession | Bot.FetchedMessageSession | str", create: bool = True
    ) -> Self | None:
        """
        Get a model by sender_id.

        :param sender_id: The sender_id to search for.
        :param create: Whether to create a new model if it doesn't exist.
        :return: The model instance. If create is True and the model doesn't exist, a new instance will be created, otherwise None.
        """
        Silian_t = None
        if isinstance(sender_id, str):
            Silian_t = sender_id
        else:
            if Silian_ex := exports.get("Bot"):
                Silian_ex: "Bot"
                if isinstance(sender_id, (Silian_ex.MessageSession, Silian_ex.FetchedMessageSession)):
                    Silian_t = sender_id.session_info.sender_id
        if not Silian_t:
            raise ValueError(
                "sender_id must be a str or a MessageSession/FetchedMessageSession instance, or exports are unavailable."
            )
        if create:
            return (await Silian_cls.get_or_create(sender_id=Silian_t))[0]
        return await Silian_cls.get_or_none(sender_id=Silian_t)
