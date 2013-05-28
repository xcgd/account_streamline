openerp.account_streamline = function(instance)
{
    var QWeb = instance.web.qweb;
    instance.web.account_streamline = instance.web.account_streamline || {};
    instance.web.views.add('tree_account_streamline_reconciliation', 'instance.web.account_streamline.ReconcileListView');

    instance.web.account_streamline.ReconcileListView = instance.web.ListView.extend({
        init: function()
        {
            this._super.apply(this, arguments);
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
            });
            this.$(".oe_account_streamline_recom_mark_as_reconciled").click(function() {
                console.log("RECON MARK AS RECONCILE");
            });
            return tmp;
        },
    });
};
