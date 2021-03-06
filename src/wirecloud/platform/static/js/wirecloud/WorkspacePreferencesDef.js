/*
 *     Copyright (c) 2008-2014 CoNWeT Lab., Universidad Politécnica de Madrid
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

/*global Wirecloud*/

(function () {

    "use strict";

    var WorkspacePreferencesDef = function WorkspacePreferencesDef(definitions, args) {
        var extra_prefs, empty_params, i, param, workspace = args[1];

        extra_prefs = Wirecloud.PreferenceManager.processDefinitions(workspace.workspaceState.extra_prefs);
        if (Array.isArray(args[2]) && args[2].length > 0) {
            empty_params = args[2];
            definitions = {};
            for (i = 0; i < empty_params.length; i += 1) {
                param = empty_params[i];
                definitions[param] = extra_prefs[param];
            }
        } else if (workspace.workspaceState != null) {
            definitions = Wirecloud.Utils.merge(definitions, extra_prefs);
        }
        Wirecloud.PreferencesDef.call(this, definitions);
    };
    WorkspacePreferencesDef.prototype = new Wirecloud.PreferencesDef();

    WorkspacePreferencesDef.prototype.buildPreferences = function buildPreferences(values, workspace) {
        return new Wirecloud.WorkspacePreferences(this, workspace, values);
    };

    Wirecloud.WorkspacePreferencesDef = WorkspacePreferencesDef;

})();
