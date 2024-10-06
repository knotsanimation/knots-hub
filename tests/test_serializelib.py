import dataclasses
from pathlib import Path

from knots_hub import serializelib


def test__Uninitialized():

    f = serializelib.Uninitialized
    assert not f


def test__mkfields():

    def sr(v):
        return v

    def usr(v, ctx):
        return v

    @dataclasses.dataclass
    class TestSerialize:
        hello: list[str] = serializelib.mkfield(
            serializer=sr,
            unserializer=usr,
            doc="wow!",
            typehint="list[str]",
        )
        from_the: str = serializelib.mkfield(
            serializer=str,
            unserializer=usr,
        )
        other_side: float = serializelib.FloatField()

    field_hello = dataclasses.fields(TestSerialize)[0]
    assert serializelib.get_field_typehint(field_hello) == "list[str]"
    assert serializelib.get_field_doc(field_hello) == "wow!"

    instance = TestSerialize()
    assert instance.hello is serializelib.Uninitialized


def test__io(tmp_path):

    @dataclasses.dataclass
    class SomeAlbum:
        playground: Path = serializelib.PathField()
        our_love: float = serializelib.FloatField("track 2")
        goodbye: str = serializelib.StrField("track 3")
        dirty_little_animals: list[Path] = serializelib.PathListField()

    def post_process(d):
        d["%%added%%"] = True
        return d

    def pre_process(d):
        del d["%%added%%"]
        return d

    instance = SomeAlbum(playground=Path())
    instance.our_love = 3.38
    serialized = serializelib.serialize(instance, post_process=post_process)
    assert "%%added%%" in serialized

    context = serializelib.UnserializeContext({}, Path())
    unserialized = serializelib.unserialize(
        serialized,
        data_class=SomeAlbum,
        context=context,
        pre_process=pre_process,
    )

    assert unserialized == instance

    disk_path = tmp_path / "some_album.json"
    serializelib.write_to_disk(instance, disk_path, post_process=post_process)
    assert disk_path.exists()

    unserialized_disk = serializelib.read_from_disk(
        SomeAlbum,
        disk_path,
        pre_process=pre_process,
    )
    assert unserialized_disk == instance

    instance_updated = dataclasses.replace(instance, goodbye="forever?")
    serializelib.update_disk(instance_updated, disk_path)

    unserialized_disk = serializelib.read_from_disk(SomeAlbum, disk_path)
    assert unserialized_disk == instance_updated
