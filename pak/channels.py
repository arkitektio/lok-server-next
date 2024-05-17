from ekke.channel import build_channel

stash_changed, stash_changed_listen = build_channel("item_added")
