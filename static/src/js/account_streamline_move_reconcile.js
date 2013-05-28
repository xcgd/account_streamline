openerp.account_streamline = function(instance)
{
    var _t = instance.web._t;
    var _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    instance.web.account_streamline = instance.web.account_streamline || {};
    instance.web.views.add('tree_account_streamline_reconciliation', 'instance.web.account_streamline.ReconcileListView');

    instance.web.account_streamline.ReconcileListView = instance.web.ListView.extend({
        init: function()
        {
            this._super.apply(this, arguments);
            var self = this;
            this.current_partner = null;
            this.on('record_selected', this, function() {
                if (self.get_selected_ids().length >= 2) {
                    self.$(".oe_account_streamline_recon_reconcile").removeAttr("disabled");
                    console.log("Button Clickable");
                } else {
                    self.$(".oe_account_streamline_recon_reconcile").attr("disabled", "");
                    console.log("Button Unclickable");
                }
            });
        },
        load_list: function()
        {
            var self = this;
            var tmp = this._super.apply(this, arguments);
            this.$el.prepend(QWeb.render("AccountStreamlineReconciliation", {widget: this}));
            this.$(".oe_account_streamline_recon_previous").click(function() {
                console.log("RECON PREVIOUS");
            });
            this.$(".oe_account_streamline_recon_next").click(function() {
                console.log("RECON NEXT");
            });
            this.$(".oe_account_streamline_recon_reconcile").click(function() {
                console.log("RECON RECONCILE");
                self.reconcile();
            });
            this.$(".oe_account_streamline_recon_mark_as_reconciled").click(function() {
                console.log("RECON MARK AS RECONCILE");
            });
            return tmp;
        },
        reconcile: function()
        {
            var self = this;
            var ids = this.get_selected_ids();

            console.log("Trying to reconcile...")
            console.log(ids);

            new instance.web.Model("ir.model.data").call("get_object_reference", ["account", "action_view_account_move_line_reconcile"]).then(function(result)
            {
                var additional_context = _.extend({
                    active_id: ids[0],
                    active_ids: ids,
                    active_model: self.model
                });
                return self.rpc("/web/action/load", {
                    action_id: result[1],
                    context: additional_context
                }).done(function (result) {
                    result.context = instance.web.pyeval.eval('contexts', [result.context, additional_context]);
                    result.flags = result.flags || {};
                    result.flags.new_window = true;
                    return self.do_action(result, {
                        on_close: function () {
                            self.do_search(self.last_domain, self.last_context, self.last_group_by);
                        }
                    });
                });
            });
        },
        do_search: function(domain, context, group_by)
        {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            var mod = new instance.web.Model("account.move.line", context, domain);
            return mod.call("list_partners_to_reconcile", []).then(function(result) {
                var current = self.current_partner !== null ? self.partners[self.current_partner][0] : null;
                self.partners = result;
                var index = _.find(_.range(self.partners.length), function(el) {
                    if (current === self.partners[el][0])
                        return true;
                });
                //if (index !== undefined)
                //{
                //    self.current_partner = index;
                //}
                //else
                //{
                //    self.search_by_partner();
                //}
                //self.search_by_partner();
            });
        },
        do_select: function (ids, records)
        {
            this.trigger('record_selected');
            this._super.apply(this, arguments);
        },
    });
};
