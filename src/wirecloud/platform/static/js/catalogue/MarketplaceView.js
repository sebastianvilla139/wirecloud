/*
 *     (C) Copyright 2012 Universidad Politécnica de Madrid
 *
 *     This file is part of Wirecloud Platform.
 *
 *     Wirecloud Platform is free software: you can redistribute it and/or
 *     modify it under the terms of the GNU Affero General Public License as
 *     published by the Free Software Foundation, either version 3 of the
 *     License, or (at your option) any later version.
 *
 *     Wirecloud is distributed in the hope that it will be useful, but WITHOUT
 *     ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 *     FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
 *     License for more details.
 *
 *     You should have received a copy of the GNU Affero General Public License
 *     along with Wirecloud Platform.  If not, see
 *     <http://www.gnu.org/licenses/>.
 *
 */

/*global StyledElements, LayoutManagerFactory, Wirecloud, gettext*/

(function () {

    "use strict";

    var MarketplaceView, onGetStoresSuccess, onGetStoresFailure;

    onGetStoresSuccess = function onGetStoresSuccess(options, view_info) {
        var info, old_views, view_element, view_constructor, first_element = null;

        this.loading = false;
        this.error = false;

        old_views = this.viewsByName;
        this.viewsByName = {};

        for (info in view_info) {

            view_element = view_info[info];

            if (info in old_views) {
                this.viewsByName[info] = old_views[info];
                delete old_views[info];
            } else {
                view_constructor = Wirecloud.MarketManager.getMarketViewClass(view_element.type);
                this.viewsByName[info] = this.alternatives.createAlternative({alternative_constructor: view_constructor, containerOptions: {catalogue: this, marketplace_desc: view_element}});
            }

            this.number_of_alternatives += 1;
            if (first_element === null) {
                first_element = this.viewsByName[info];
            }
        }

        for (info in old_views) {
            this.alternatives.removeAlternative(old_views[info]);
            old_views[info].destroy();
        }

        if (this.alternatives.getCurrentAlternative() === this.emptyAlternative) {
            this.alternatives.showAlternative(this.viewsByName.local);
        }

        // Refresh wirecloud header as current marketplace may have been changed
        LayoutManagerFactory.getInstance().header.refresh();

        if (typeof options.onSuccess === 'function') {
            options.onSuccess();
        }
        if (typeof options.onComplete === 'function') {
            options.onComplete();
        }
    };

    onGetStoresFailure = function onGetStoresFailure(options, msg) {
        this.loading = false;
        this.error = true;

        LayoutManagerFactory.getInstance().header.refresh();
        if (typeof options.onFailure === 'function') {
            options.onFailure();
        }
        if (typeof options.onFailure === 'function') {
            options.onComplete();
        }
    };


    MarketplaceView = function MarketplaceView(id, options) {
        options.id = 'marketplace';
        StyledElements.Alternative.call(this, id, options);

        this.viewsByName = {};
        this.alternatives = new StyledElements.StyledAlternatives();
        this.emptyAlternative = this.alternatives.createAlternative();
        this.alternatives.addEventListener('postTransition', function () {
            LayoutManagerFactory.getInstance().header.refresh();
        });
        this.appendChild(this.alternatives);

        this.marketMenu = new StyledElements.PopupMenu();
        this.marketMenu.append(new Wirecloud.ui.MarketplaceViewMenuItems(this));

        this.addEventListener('show', function (view) {
            if (!view.loading && !view.error) {
                view.alternatives.getCurrentAlternative().refresh_if_needed();
            }
        });

        this.number_of_alternatives = 0;
        this.loading = true;
        this.error = false;
        Wirecloud.MarketManager.getMarkets(onGetStoresSuccess.bind(this, {}), onGetStoresFailure.bind(this, {}));
    };

    MarketplaceView.prototype = new StyledElements.Alternative();

    MarketplaceView.prototype.view_name = 'marketplace';

    MarketplaceView.prototype.getBreadcrum = function () {
        var label, breadcrum, user;

        user = null;
        if (this.loading) {
            label = gettext('loading...');
        } else if (this.error) {
            label = gettext('list not available');
        } else if (this.number_of_alternatives > 0) {
            label = this.alternatives.getCurrentAlternative().getLabel();
            user = this.alternatives.getCurrentAlternative().desc.user;
        } else {
            label = gettext('no registered marketplace');
        }

        breadcrum = [{'label': 'marketplace'}];
        if (user != null) {
            breadcrum.push({'label': user});
        }

        breadcrum.push({
            'label': label,
            'menu': this.marketMenu
        });

        // If no alternatives exist, it is no posible to have an extra breadcrum
        if (!this.loading && !this.error && this.number_of_alternatives > 0) {
            if (typeof this.alternatives.getCurrentAlternative().getExtraBreadcrum === 'function') {
                breadcrum = breadcrum.concat(this.alternatives.getCurrentAlternative().getExtraBreadcrum());
            }
        }
        return breadcrum;
    };

    MarketplaceView.prototype.refreshViewInfo = function refreshViewInfo(options) {

        if (this.loading) {
            return;
        }

        if (typeof options !== 'object') {
            options = {};
        }

        this.loading = true;
        LayoutManagerFactory.getInstance().header.refresh();

        this.number_of_alternatives = 0;

        Wirecloud.MarketManager.getMarkets(onGetStoresSuccess.bind(this, options), onGetStoresFailure.bind(this, options));
    };

    MarketplaceView.prototype.addMarket = function addMarket(market_info) {
        var view_constructor = Wirecloud.MarketManager.getMarketViewClass(market_info.type);
        this.viewsByName[market_info.name] = this.alternatives.createAlternative({alternative_constructor: view_constructor, containerOptions: {catalogue: this, marketplace_desc: market_info}});

        this.number_of_alternatives += 1;
        this.alternatives.showAlternative(this.viewsByName[market_info.name]);
    };

    window.MarketplaceView = MarketplaceView;
})();