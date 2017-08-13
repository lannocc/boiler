# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

from steem.amount import Amount

import ag.logging as log


def have_bandwidth(steem, account):
    '''
        Determine if the given account has enough bandwidth to do stuff.
        Note that this is just an estimate to return approximately >20% bandwidth remaining.
    '''
    # FIXME: rewrite this once we get a better calculation for determining available bandwidth

    props = steem.get_dynamic_global_properties()
    log.debug("got global properties", props=props)

    total_vests = Amount(props['total_vesting_shares']).amount
    max_bandwidth = int(props['max_virtual_bandwidth'])

    vests = Amount(account['vesting_shares']).amount
    bw_post = steem.get_account_bandwidth(account.name, "post")
    bw_forum = steem.get_account_bandwidth(account.name, "forum")
    bw_market = steem.get_account_bandwidth(account.name, "market")
    log.debug("account bandwidth information", vests=vests, post=bw_post, forum=bw_forum, market=bw_market)

    bw_allocated = vests / total_vests
    bw_used = (int(bw_market['average_bandwidth']) + int(bw_forum['average_bandwidth'])) / max_bandwidth
    ratio = bw_used / bw_allocated
    log.debug("bandwidth calculation", allocated=bw_allocated, used=bw_used, ratio=ratio)

    return ratio < 9

